#!/usr/bin/env python3
"""
Digital Twin of Transformer - Starter Template
Complete implementation of data acquisition, modeling, and analysis
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
from sklearn.ensemble import IsolationForest
import os
import serial
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TransformerSpecs:
    """Transformer specifications"""
    transformer_id: str
    capacity_mva: float
    voltage_primary_kv: float
    voltage_secondary_kv: float
    cooling_system: str  # ONAN, ONAF, OFAF
    age_years: int
    nominal_current_primary: float
    nominal_current_secondary: float
    core_loss_watts: float
    copper_loss_watts: float
    tank_volume_liters: float


@dataclass
class SensorReading:
    """Real-time sensor data"""
    timestamp: str
    voltage_primary_kv: float
    current_primary_a: float
    voltage_secondary_kv: float
    current_secondary_a: float
    oil_temperature_c: float
    ambient_temperature_c: float
    cooling_active: bool
    pressure_bar: float = 0.0


@dataclass
class OilQuality:
    """Oil quality parameters"""
    moisture_ppm: float
    acid_number_mg_koh: float
    breakdown_voltage_kv: float = 0.0
    viscosity_cst: float = 0.0


# ============================================================================
# ELECTROMAGNETIC MODEL
# ============================================================================

class ElectromagneticModel:
    """Simulate transformer electrical performance"""
    
    def __init__(self, specs: TransformerSpecs):
        self.specs = specs
        self.P_core = specs.core_loss_watts
        self.P_copper = specs.copper_loss_watts
        self.S_nom = specs.capacity_mva * 1000  # Convert to kW
    
    def calculate_losses(self, voltage_pu: float, current_pu: float) -> Dict:
        """Calculate core and copper losses"""
        P_core = self.P_core * (voltage_pu ** 2)
        P_copper = self.P_copper * (current_pu ** 2)
        P_total = P_core + P_copper
        
        return {
            'core_loss_w': P_core,
            'copper_loss_w': P_copper,
            'total_loss_w': P_total,
            'loss_percent': (P_total / self.S_nom) * 100
        }
    
    def calculate_efficiency(self, output_kw: float, voltage_pu: float, 
                           current_pu: float) -> float:
        """Calculate transformer efficiency"""
        losses = self.calculate_losses(voltage_pu, current_pu)
        total_loss_kw = losses['total_loss_w'] / 1000
        
        input_power = output_kw + total_loss_kw
        if input_power <= 0:
            return 0.0
        
        efficiency = (output_kw / input_power) * 100
        return min(100, max(0, efficiency))
    
    def process_reading(self, reading: SensorReading) -> Dict:
        """Process sensor reading and calculate electrical metrics"""
        voltage_pu = reading.voltage_primary_kv / self.specs.voltage_primary_kv
        current_pu = reading.current_primary_a / self.specs.nominal_current_primary
        
        power_out_kw = (reading.voltage_primary_kv * reading.current_primary_a) / 1000
        
        losses = self.calculate_losses(voltage_pu, current_pu)
        efficiency = self.calculate_efficiency(power_out_kw, voltage_pu, current_pu)
        load_percent = current_pu * 100
        
        return {
            'voltage_pu': voltage_pu,
            'current_pu': current_pu,
            'load_percent': load_percent,
            'power_out_kw': power_out_kw,
            'efficiency_percent': efficiency,
            **losses
        }


# ============================================================================
# THERMAL MODEL
# ============================================================================

class ThermalModel:
    """Simulate temperature dynamics"""
    
    def __init__(self, specs: TransformerSpecs):
        self.specs = specs
        self.V = specs.tank_volume_liters / 1000  # m³
        self.rho = 860  # Oil density kg/m³
        self.c = 1900  # Specific heat J/kg·K
        self.mass = self.V * self.rho  # kg
        
        # Heat transfer parameters
        self.h_natural = 15  # W/m²·K
        self.h_forced = 25   # W/m²·K
        self.area = 5.0      # m²
    
    def heat_dissipation(self, oil_temp: float, ambient_temp: float, 
                        cooling_active: bool) -> float:
        """Calculate heat loss"""
        delta_t = oil_temp - ambient_temp
        h = self.h_forced if cooling_active else self.h_natural
        return h * self.area * delta_t
    
    def predict_oil_temperature(self, current_temp: float, power_loss_w: float,
                               ambient_temp: float, cooling_active: bool,
                               time_minutes: float) -> float:
        """Predict oil temperature after time_minutes"""
        dt = time_minutes * 60  # Convert to seconds
        
        # Heat dissipation
        Q_loss = self.heat_dissipation(current_temp, ambient_temp, cooling_active)
        
        # Temperature change: dT = (P - Q) / (m * c) * dt
        delta_temp = (power_loss_w - Q_loss) / (self.mass * self.c) * dt
        
        new_temp = current_temp + delta_temp
        return np.clip(new_temp, -10, 110)  # Realistic bounds
    
    def calculate_hot_spot_temp(self, oil_temp: float, load_percent: float) -> float:
        """Estimate winding hot spot temperature"""
        # Simplified: hot spot = oil temp + temperature rise
        temp_rise = 10 + 1.5 * (load_percent / 100) * 40
        return oil_temp + temp_rise
    
    def process_reading(self, reading: SensorReading, power_loss_w: float,
                       previous_oil_temp: float) -> Dict:
        """Process thermal reading"""
        oil_temp_next = self.predict_oil_temperature(
            current_temp=previous_oil_temp,
            power_loss_w=power_loss_w,
            ambient_temp=reading.ambient_temperature_c,
            cooling_active=reading.cooling_active,
            time_minutes=5  # Assuming 5-minute updates
        )
        
        temp_rise = reading.oil_temperature_c - reading.ambient_temperature_c
        
        return {
            'oil_temperature_c': reading.oil_temperature_c,
            'predicted_oil_temp_c': oil_temp_next,
            'ambient_temperature_c': reading.ambient_temperature_c,
            'temperature_rise_c': temp_rise,
            'cooling_active': reading.cooling_active
        }


# ============================================================================
# DEGRADATION MODEL
# ============================================================================

class DegradationModel:
    """Estimate transformer aging and remaining life"""
    
    def __init__(self):
        self.Ea = 126000  # Activation energy J/mol
        self.R = 8.314    # Gas constant
        self.T_ref = 353.15  # 80°C in Kelvin
        self.rated_life_years = 30
    
    def aging_rate(self, hot_spot_temp: float) -> float:
        """Arrhenius equation for aging rate"""
        T_k = hot_spot_temp + 273.15
        exponent = (self.Ea / self.R) * (1/self.T_ref - 1/T_k)
        return np.exp(exponent)
    
    def remaining_life(self, age_years: float, hot_spot_temp: float,
                      load_hours_per_day: float = 16.0) -> float:
        """Estimate remaining useful life"""
        aging_rate = self.aging_rate(hot_spot_temp)
        degradation_per_year = (load_hours_per_day / 24) * aging_rate
        
        current_degradation = age_years / self.rated_life_years
        remaining_degradation = max(0, 1.0 - current_degradation)
        
        if degradation_per_year <= 0:
            return 0.0
        
        remaining_years = remaining_degradation / degradation_per_year
        return max(0, remaining_years)
    
    def health_index(self, age_years: float, hot_spot_temp: float,
                    oil_moisture_ppm: float, acid_number: float) -> float:
        """Combined health index (0-100)"""
        # Age component
        age_score = max(0, 100 * (1 - age_years / 30))
        
        # Temperature component
        temp_score = max(0, 100 - (hot_spot_temp - 65) * 2) if hot_spot_temp > 65 else 100
        
        # Oil quality components
        moisture_score = max(0, 100 - (oil_moisture_ppm / 10))
        acid_score = max(0, 100 - (acid_number * 500))
        
        # Weighted average
        health = (0.3 * age_score + 0.3 * temp_score + 
                 0.2 * moisture_score + 0.2 * acid_score)
        
        return min(100, max(0, health))
    
    def process_assessment(self, age_years: float, hot_spot_temp: float,
                          oil_quality: OilQuality) -> Dict:
        """Complete degradation assessment"""
        remaining_life = self.remaining_life(age_years, hot_spot_temp)
        health = self.health_index(age_years, hot_spot_temp,
                                  oil_quality.moisture_ppm,
                                  oil_quality.acid_number_mg_koh)
        
        if health >= 80:
            condition = "EXCELLENT"
        elif health >= 60:
            condition = "GOOD"
        elif health >= 40:
            condition = "FAIR"
        elif health >= 20:
            condition = "POOR"
        else:
            condition = "CRITICAL"
        
        return {
            'age_years': age_years,
            'hot_spot_temperature_c': hot_spot_temp,
            'health_index': health,
            'condition': condition,
            'remaining_life_years': remaining_life
        }

# ============================================================================
# MACHINE LEARNING ANOMALY DETECTION
# ============================================================================

class MLAnomalyDetector:

    def __init__(self):

        self.model = IsolationForest(
            contamination=0.05,
            random_state=42
        )

        self.trained = False

    def generate_training_data(self):

        data = []

        for i in range(500):

            temperature = np.random.normal(65, 5)

            current = np.random.normal(400, 40)

            voltage = np.random.normal(11, 0.1)

            efficiency = np.random.normal(97, 1)

            data.append([
                temperature,
                current,
                voltage,
                efficiency
            ])

        return np.array(data)

    def train_model(self):

        X = self.generate_training_data()

        self.model.fit(X)

        self.trained = True

    def detect_anomaly(self,
                       temperature,
                       current,
                       voltage,
                       efficiency):

        if not self.trained:
            self.train_model()

        sample = [[
            temperature,
            current,
            voltage,
            efficiency
        ]]

        prediction = self.model.predict(sample)

        return prediction[0]

# ============================================================================
# DIGITAL TWIN ENGINE
# ============================================================================

class DigitalTwinEngine:
    """Integrate all models for complete digital twin"""
    
    def __init__(self, specs: TransformerSpecs):
        self.specs = specs
        self.em_model = ElectromagneticModel(specs)
        self.thermal_model = ThermalModel(specs)
        self.degradation_model = DegradationModel()
        self.ml_detector = MLAnomalyDetector()
        
        self.current_state = {
            'timestamp': None,
            'electrical': {},
            'thermal': {},
            'degradation': {},
            'faults': [],
            'health_status': 'UNKNOWN'
        }
    
    def update(self, reading: SensorReading, oil_quality: OilQuality) -> Dict:
        """Update digital twin with new sensor data"""
        
        # Electrical calculations
        em_results = self.em_model.process_reading(reading)
        
        # Thermal calculations
        previous_oil_temp = self.current_state['thermal'].get('oil_temperature_c', 65)
        thermal_results = self.thermal_model.process_reading(
            reading, em_results['total_loss_w'], previous_oil_temp
        )
        
        # Hot spot temperature
        hot_spot = self.thermal_model.calculate_hot_spot_temp(
            thermal_results['oil_temperature_c'],
            em_results['load_percent']
        )
        thermal_results['hot_spot_temperature_c'] = hot_spot
        
        # Degradation assessment
        degradation_results = self.degradation_model.process_assessment(
            self.specs.age_years,
            hot_spot,
            oil_quality
        )

        # ML anomaly detection

        ml_result = self.ml_detector.detect_anomaly(
            reading.oil_temperature_c,
            reading.current_primary_a,
            reading.voltage_primary_kv,
            em_results['efficiency_percent']

        )
        
        # Detect faults
        faults = self._detect_faults(em_results, thermal_results, 
                                    degradation_results, oil_quality)
        
        # ML anomaly fault
        if ml_result == -1:
            faults.append({
                'type': 'ML_ANOMALY_DETECTED',
                'severity': 'HIGH',
                'value': reading.oil_temperature_c,
                'recommendation':
                'Machine learning detected abnormal operating behavior'
            })

        # Update state
        self.current_state = {
            'timestamp': reading.timestamp,
            'electrical': em_results,
            'thermal': {**thermal_results, 'hot_spot_temperature_c': hot_spot},
            'degradation': degradation_results,
            'faults': faults,
            'health_status': degradation_results['condition']
        }
        
        return self.current_state
    
    def _detect_faults(self, em: Dict, thermal: Dict, degradation: Dict,
                      oil: OilQuality) -> List[Dict]:
        """Detect fault conditions"""
        faults = []
        
        # Temperature fault
        if thermal['hot_spot_temperature_c'] > 95:
            faults.append({
                'type': 'OVER_TEMPERATURE',
                'severity': 'CRITICAL',
                'value': thermal['hot_spot_temperature_c'],
                'threshold': 95,
                'recommendation': 'Reduce load or activate cooling'
            })
        
        # Oil moisture
        if oil.moisture_ppm > 500:
            faults.append({
                'type': 'HIGH_MOISTURE',
                'severity': 'WARNING',
                'value': oil.moisture_ppm,
                'recommendation': 'Schedule oil drying'
            })
        
        # Acid number
        if oil.acid_number_mg_koh > 0.1:
            faults.append({
                'type': 'OIL_DEGRADATION',
                'severity': 'CRITICAL',
                'value': oil.acid_number_mg_koh,
                'recommendation': 'Replace oil immediately'
            })
        
        # Efficiency drop
        if em['efficiency_percent'] < 92:
            faults.append({
                'type': 'EFFICIENCY_DROP',
                'severity': 'WARNING',
                'value': em['efficiency_percent'],
                'recommendation': 'Investigate for core or winding damage'
            })
        
        # Low remaining life
        if degradation['remaining_life_years'] < 2:
            faults.append({
                'type': 'END_OF_LIFE',
                'severity': 'HIGH',
                'value': degradation['remaining_life_years'],
                'recommendation': 'Plan for transformer replacement'
            })
        
        return faults
    
    def get_status_report(self) -> Dict:
        """Generate status report"""
        return {
            'transformer_id': self.specs.transformer_id,
            'timestamp': self.current_state['timestamp'],
            'overall_health': self.current_state['health_status'],
            'summary': {
                'load_percent': self.current_state['electrical'].get('load_percent', 0),
                'efficiency': self.current_state['electrical'].get('efficiency_percent', 0),
                'oil_temperature': self.current_state['thermal'].get('oil_temperature_c', 0),
                'hot_spot_temperature': self.current_state['thermal'].get('hot_spot_temperature_c', 0),
                'health_index': self.current_state['degradation'].get('health_index', 0),
                'remaining_life_years': self.current_state['degradation'].get('remaining_life_years', 0),
            },
            'active_faults': self.current_state['faults'],
            'recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate maintenance recommendations"""
        recommendations = []
        
        health = self.current_state['degradation'].get('health_index', 100)
        remaining_life = self.current_state['degradation'].get('remaining_life_years', 0)
        faults = self.current_state['faults']
        
        # Check health
        if health < 40:
            recommendations.append("URGENT: Schedule immediate inspection")
        elif health < 60:
            recommendations.append("Plan oil analysis within 1 month")
        
        # Check remaining life
        if remaining_life < 2:
            recommendations.append(f"Plan transformer replacement in {remaining_life:.1f} years")
        
        # Check critical faults
        critical_faults = [f for f in faults if f['severity'] == 'CRITICAL']
        for fault in critical_faults:
            recommendations.append(f"Critical: {fault['recommendation']}")
        
        return recommendations if recommendations else ["System operating normally"]

# ============================================================================
# REAL-TIME SENSOR DATA FROM ESP32
# ============================================================================

def read_sensor_data():

    try:

        # Change COM3 according to your ESP32 port
        ser = serial.Serial(
            'COM3',
            115200,
            timeout=1
        )

        line = ser.readline().decode().strip()

        data = json.loads(line)

        reading = SensorReading(

            timestamp=datetime.utcnow().isoformat(),

            voltage_primary_kv=float(
                data["primary_voltage"]
            ),

            current_primary_a=float(
                data["primary_current"]
            ),

            voltage_secondary_kv=float(
                data["secondary_voltage"]
            ),

            current_secondary_a=float(
                data["secondary_current"]
            ),

            oil_temperature_c=float(
                data["oil_temperature"]
            ),

            ambient_temperature_c=float(
                data["ambient_temperature"]
            ),

            cooling_active=bool(
                data["cooling_active"]
            ),

            pressure_bar=float(
                data["pressure"]
            )
        )

        oil_quality = OilQuality(

            moisture_ppm=float(
                data["moisture_ppm"]
            ),

            acid_number_mg_koh=float(
                data["acid_number"]
            ),

            breakdown_voltage_kv=float(
                data["breakdown_voltage"]
            ),

            viscosity_cst=float(
                data["viscosity"]
            )
        )

        return reading, oil_quality

    except Exception as e:

        print("Sensor Read Error:", e)

        return None, None
    
# ============================================================================
# REAL-TIME DIGITAL TWIN EXECUTION
# ============================================================================

def demo():

    specs = TransformerSpecs(

        transformer_id="TX-001",

        capacity_mva=100,

        voltage_primary_kv=11,

        voltage_secondary_kv=0.4,

        cooling_system="ONAF",

        age_years=8,

        nominal_current_primary=525,

        nominal_current_secondary=144000,

        core_loss_watts=5000,

        copper_loss_watts=25000,

        tank_volume_liters=50000
    )

    twin = DigitalTwinEngine(specs)

    print("=" * 70)

    print("REAL-TIME DIGITAL TWIN OF TRANSFORMER")

    print("=" * 70)

    while True:

        reading, oil_quality = read_sensor_data()

        if reading is None:
            continue

        state = twin.update(
            reading,
            oil_quality
        )

        report = twin.get_status_report()

        print(f"\n[{report['timestamp']}]")

        print(
            f"Transformer ID: "
            f"{report['transformer_id']}"
        )

        print(
            f"Overall Health: "
            f"{report['overall_health']}"
        )

        print("\nPerformance Metrics:")

        print(
            f"Load: "
            f"{report['summary']['load_percent']:.1f}%"
        )

        print(
            f"Efficiency: "
            f"{report['summary']['efficiency']:.2f}%"
        )

        print(
            f"Oil Temp: "
            f"{report['summary']['oil_temperature']:.1f}°C"
        )

        print(
            f"Hot Spot Temp: "
            f"{report['summary']['hot_spot_temperature']:.1f}°C"
        )

        print("\nCondition Metrics:")

        print(
            f"Health Index: "
            f"{report['summary']['health_index']:.1f}/100"
        )

        print(
            f"Remaining Life: "
            f"{report['summary']['remaining_life_years']:.1f} years"
        )

        if report['active_faults']:

            print("\n⚠ ACTIVE FAULTS:")

            for fault in report['active_faults']:

                print(
                    f"- {fault['type']} "
                    f"({fault['severity']})"
                )

                print(
                    f"  Recommendation: "
                    f"{fault['recommendation']}"
                )

        print("\nRecommendations:")

        for rec in report['recommendations']:

            print(f"• {rec}")

        print("-" * 70)

if __name__ == "__main__":

    demo()