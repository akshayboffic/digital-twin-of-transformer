# ============================================================================
# ELECTROMAGNETIC MODEL
# ============================================================================

from pyparsing import Dict
from digital_twin_project.models.integrated_twin import TransformerSpecs


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

