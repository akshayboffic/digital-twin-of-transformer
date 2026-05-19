# ============================================================================
# DEGRADATION MODEL
# ============================================================================

from pyparsing import Dict
from digital_twin_project.models.integrated_twin import OilQuality


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
