"""
FHIR Observation Generator for Blood Pressure measurements
Generates FHIR-compliant JSON observations following the HL7 FHIR standard
"""
import json
import random
import uuid
from datetime import datetime
from typing import Dict, Optional

from data_generator.patients import (
    PATIENTS,
    get_practitioner_for_patient
)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import LOINC_CODES, BP_THRESHOLDS


def generate_blood_pressure_values(simulate_anomaly: bool = False) -> tuple:
    """
    Generate realistic blood pressure values.
    
    Args:
        simulate_anomaly: If True, has 30% chance to generate abnormal values
    
    Returns:
        Tuple of (systolic, diastolic) values in mmHg
    """
    if simulate_anomaly and random.random() < 0.3:
        # Generate abnormal values (either too high or too low)
        anomaly_type = random.choice(["hypertension", "hypotension"])
        
        if anomaly_type == "hypertension":
            systolic = random.randint(145, 180)
            diastolic = random.randint(92, 120)
        else:
            systolic = random.randint(70, 88)
            diastolic = random.randint(45, 58)
    else:
        # Generate normal values
        systolic = random.randint(95, 135)
        diastolic = random.randint(62, 88)
    
    return systolic, diastolic


def create_fhir_observation(
    patient_id: str,
    systolic: int,
    diastolic: int,
    effective_datetime: Optional[datetime] = None
) -> Dict:
    """
    Create a FHIR Observation resource for blood pressure.
    
    Based on: https://www.hl7.org/fhir/observation-example-bloodpressure.json.html
    
    Args:
        patient_id: The patient's unique identifier
        systolic: Systolic blood pressure value in mmHg
        diastolic: Diastolic blood pressure value in mmHg
        effective_datetime: When the observation was made (defaults to now)
    
    Returns:
        FHIR Observation resource as a dictionary
    """
    if effective_datetime is None:
        effective_datetime = datetime.now()
    
    practitioner = get_practitioner_for_patient(patient_id)
    
    observation = {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "meta": {
            "profile": [
                "http://hl7.org/fhir/StructureDefinition/vitalsigns"
            ]
        },
        "status": "final",
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs"
                    }
                ]
            }
        ],
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": LOINC_CODES["blood_pressure_panel"],
                    "display": "Blood pressure panel with all children optional"
                }
            ],
            "text": "Blood pressure systolic & diastolic"
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "effectiveDateTime": effective_datetime.isoformat(),
        "performer": [
            {
                "reference": f"Practitioner/{practitioner['id']}" if practitioner else None
            }
        ],
        "component": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": LOINC_CODES["systolic"],
                            "display": "Systolic blood pressure"
                        }
                    ]
                },
                "valueQuantity": {
                    "value": systolic,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                }
            },
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": LOINC_CODES["diastolic"],
                            "display": "Diastolic blood pressure"
                        }
                    ]
                },
                "valueQuantity": {
                    "value": diastolic,
                    "unit": "mmHg",
                    "system": "http://unitsofmeasure.org",
                    "code": "mm[Hg]"
                }
            }
        ]
    }
    
    return observation


def generate_observation_for_patient(patient_id: str, simulate_anomaly: bool = True) -> Dict:
    """
    Generate a complete FHIR observation for a specific patient.
    
    Args:
        patient_id: The patient's unique identifier
        simulate_anomaly: Whether to simulate abnormal values sometimes
    
    Returns:
        FHIR Observation resource
    """
    systolic, diastolic = generate_blood_pressure_values(simulate_anomaly)
    return create_fhir_observation(patient_id, systolic, diastolic)


def generate_observations_for_all_patients(simulate_anomaly: bool = True) -> list:
    """
    Generate FHIR observations for all defined patients.
    
    Args:
        simulate_anomaly: Whether to simulate abnormal values sometimes
    
    Returns:
        List of FHIR Observation resources
    """
    observations = []
    for patient in PATIENTS:
        observation = generate_observation_for_patient(patient["id"], simulate_anomaly)
        observations.append(observation)
    return observations


if __name__ == "__main__":
    # Test the generator
    print("=" * 60)
    print("Testing FHIR Blood Pressure Observation Generator")
    print("=" * 60)
    
    observations = generate_observations_for_all_patients()
    
    for obs in observations:
        systolic = obs["component"][0]["valueQuantity"]["value"]
        diastolic = obs["component"][1]["valueQuantity"]["value"]
        patient_ref = obs["subject"]["reference"]
        
        print(f"\nPatient: {patient_ref}")
        print(f"  Systolic: {systolic} mmHg")
        print(f"  Diastolic: {diastolic} mmHg")
        print(f"  Observation ID: {obs['id']}")
    
    # Print one full observation as JSON
    print("\n" + "=" * 60)
    print("Sample FHIR Observation (JSON):")
    print("=" * 60)
    print(json.dumps(observations[0], indent=2))
