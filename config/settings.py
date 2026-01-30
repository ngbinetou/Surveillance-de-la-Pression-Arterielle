"""
Configuration settings for the Blood Pressure Monitoring System
"""

# Kafka Configuration
KAFKA_CONFIG = {
    "bootstrap_servers": "localhost:9092",
    "topic": "blood_pressure_topic",
    "group_id": "blood_pressure_consumer_group"
}

# Elasticsearch Configuration
ELASTICSEARCH_CONFIG = {
    "hosts": ["http://localhost:9200"],
    "index_name": "abnormal_blood_pressure"
}

# Blood Pressure Thresholds (mmHg)
BP_THRESHOLDS = {
    "systolic": {
        "min": 90,   # Hypotension threshold
        "max": 140   # Hypertension threshold
    },
    "diastolic": {
        "min": 60,   # Hypotension threshold
        "max": 90    # Hypertension threshold
    }
}

# Data Generation Settings
GENERATION_CONFIG = {
    "num_patients": 5,
    "num_practitioners": 2,
    "interval_seconds": 5  # Generate observation every 5 seconds
}

# Storage Paths
STORAGE_CONFIG = {
    "normal_data_path": "output/normal/",
    "model_path": "models/trained_model.pkl"
}

# FHIR LOINC Codes for Blood Pressure
LOINC_CODES = {
    "blood_pressure_panel": "85354-9",
    "systolic": "8480-6",
    "diastolic": "8462-4"
}
