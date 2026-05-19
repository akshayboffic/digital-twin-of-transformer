from flask import Flask, render_template
from datetime import datetime
import sys
import os
import random

# Add project root path
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..')
    )
)

from models.integrated_twin import (
    TransformerSpecs,
    SensorReading,
    OilQuality,
    DigitalTwinEngine
)

app = Flask(__name__)

@app.route('/')

def dashboard():

    # Transformer specs
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

    # Create digital twin
    twin = DigitalTwinEngine(specs)

    # Simulated sensor reading
    reading = SensorReading(
        timestamp=datetime.utcnow().isoformat(),
        voltage_primary_kv=11.0,
        current_primary_a=random.randint(300,600),
        voltage_secondary_kv=0.4,
        current_secondary_a=140000,
        oil_temperature_c=random.randint(50,100),
        ambient_temperature_c=25,
        cooling_active=True,
        pressure_bar=1.2
    )

    oil_quality = OilQuality(
        moisture_ppm=250,
        acid_number_mg_koh=0.04
    )

    # Update twin
    state = twin.update(reading, oil_quality)

    electrical = state['electrical']
    thermal = state['thermal']
    degradation = state['degradation']
    faults = state['faults']

    recommendations = twin.get_status_report()['recommendations']

    return render_template(
        'transformer_dashboard.html',

        load=round(electrical['load_percent'], 1),

        efficiency=round(
            electrical['efficiency_percent'], 2
        ),

        oil_temp=round(
            thermal['oil_temperature_c'], 1
        ),

        hot_spot=round(
            thermal['hot_spot_temperature_c'], 1
        ),

        health_index=round(
            degradation['health_index'], 1
        ),

        remaining_life=round(
            degradation['remaining_life_years'], 1
        ),

        condition=degradation['condition'],

        faults=faults,

        recommendations=recommendations
    )

if __name__ == "__main__":
    app.run(debug=True)