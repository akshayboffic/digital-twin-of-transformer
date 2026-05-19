# Digital Twin for Transformer 

## Overview

This project presents an AI-enhanced Digital Twin framework for real-time transformer monitoring, condition assessment, anomaly detection, and predictive maintenance. The system creates a virtual representation of a physical transformer using real-time sensor inputs, mathematical modeling, thermal analysis, degradation modeling, and machine learning-based analytics.

The framework continuously monitors operational parameters such as voltage, current, oil temperature, and cooling conditions to simulate transformer behavior, evaluate equipment health, detect abnormal operating conditions, and support intelligent maintenance planning.

---

# Features

- Real-time transformer monitoring
- Electrical performance modeling
- Thermal behavior simulation
- Transformer degradation analysis
- Health index estimation
- Remaining useful life prediction
- Machine learning-based anomaly detection
- Predictive maintenance recommendations
- Flask-based dashboard visualization
- ESP32 sensor integration support
- Real-time sensor communication through USB serial interface

---

# System Architecture

The proposed architecture consists of:

- Sensor Layer
- ESP32 Data Acquisition Layer
- Digital Twin Engine
- Electrical Model
- Thermal Model
- Degradation Model
- Machine Learning Layer
- Dashboard Visualization

---

# Technologies Used

| Technology | Purpose |
|---|---|
| Python | Digital twin implementation |
| Flask | Dashboard backend |
| HTML/CSS | Dashboard UI |
| NumPy | Mathematical computations |
| Pandas | Data processing |
| Scikit-learn | Machine learning-based anomaly detection |
| Chart.js | Dashboard data visualization |
| ESP32 | Sensor data acquisition |
| PySerial | Real-time serial communication |

---

# Real-Time Parameters Monitored

- Primary Voltage
- Primary Current
- Secondary Voltage
- Secondary Current
- Oil Temperature
- Ambient Temperature
- Cooling Status
- Pressure
- Oil Moisture Content
- Oil Acid Number

---

# Mathematical Models Implemented

The digital twin framework uses:

- Transformer efficiency equations
- Electrical loss calculations
- Thermal heat transfer equations
- Hot-spot temperature estimation
- Arrhenius aging model
- Remaining useful life estimation
- Machine learning-based anomaly detection

---

# Machine Learning Integration

The project integrates Isolation Forest–based anomaly detection using Scikit-learn to identify abnormal transformer operating conditions from real-time operational data.

---

# Dashboard Features

- Live operational monitoring
- Transformer performance graphs
- Health index visualization
- Active fault alerts
- Maintenance recommendations
- Real-time parameter visualization

---

# Project Structure

```bash
project/
│
├── dashboard/
│   ├── app.py
│   └── templates/
│       └── dashboard.html
│
├── models/
│   ├── degradation_model.py
│   ├── electromagnetic_model.py
│   ├── thermal_model.py
│   ├── integrated_twin.py
│   └── real_time_digital_twin.py
│
├── requirements.txt
└── README.md
```

---

# File Descriptions

| File | Description |
|---|---|
| degradation_model.py | Transformer aging, health index, and remaining useful life estimation |
| electromagnetic_model.py | Electrical performance and transformer loss calculations |
| thermal_model.py | Thermal behavior and hot-spot temperature prediction |
| integrated_twin.py | Complete integrated transformer digital twin demonstration using simulated data |
| real_time_digital_twin.py | Real-time transformer digital twin implementation using ESP32 live sensor inputs |
| app.py | Flask-based monitoring dashboard |
| dashboard.html | Frontend dashboard visualization |

---

# Digital Twin Modes

## 1. Demonstration Mode

The `integrated_twin.py` file demonstrates the digital twin framework using simulated transformer operational data.

Run using:

```bash
python integrated_twin.py
```

---

## 2. Real-Time Monitoring Mode

The `real_time_digital_twin.py` file enables real-time transformer monitoring using ESP32-connected sensors and live operational inputs.

Run using:

```bash
python real_time_digital_twin.py
```

---

# Hardware Components

The prototype setup includes:

- Step-down Transformer
- ESP32 Development Board
- Voltage Sensor
- Current Sensor
- Temperature Sensor
- Load (Bulb/Fan)
- USB Communication Interface

---

# Installation

## Create Virtual Environment

```bash
python -m venv venv
```

---

## Activate Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / Mac

```bash
source venv/bin/activate
```

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run Dashboard

```bash
cd dashboard
python app.py
```

Open in browser:

```bash
http://127.0.0.1:5000
```

---

# Real-Time Sensor Communication

The real-time implementation receives operational data from ESP32 through serial communication using JSON-formatted sensor readings.

Example JSON sensor data:

```json
{
  "primary_voltage": 11.0,
  "primary_current": 420,
  "secondary_voltage": 0.4,
  "secondary_current": 140000,
  "oil_temperature": 68,
  "ambient_temperature": 30,
  "cooling_active": true,
  "pressure": 1.2,
  "moisture_ppm": 220,
  "acid_number": 0.04,
  "breakdown_voltage": 45,
  "viscosity": 8.5
}
```

---

# Prototype Demonstration

A functional prototype of the proposed transformer digital twin framework has been successfully developed to demonstrate:

- Real-time operational monitoring
- Thermal and degradation analysis
- Machine learning-based anomaly detection
- Predictive maintenance recommendations
- Dashboard-based visualization

---

# Future Enhancements

- Wireless IoT communication
- MQTT integration
- Cloud-based monitoring
- Historical data logging
- Advanced deep learning models
- Industrial-grade deployment
- Remote monitoring dashboard

---

# License

This project is developed for educational, research, and demonstration purposes.
