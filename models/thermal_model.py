# ============================================================================
# THERMAL MODEL
# ============================================================================

from typing import Dict
from digital_twin_project.models.integrated_twin import SensorReading, TransformerSpecs


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