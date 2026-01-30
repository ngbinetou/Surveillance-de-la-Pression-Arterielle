"""
Patient and Practitioner definitions for the Blood Pressure Monitoring System
"""
from faker import Faker
import uuid

fake = Faker('fr_FR')

# Define 5 patients with consistent data
# Define 5 patients with consistent data using deterministic UUIDs (v5)
NAMESPACE_DNS = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')

PATIENTS = [
    {
        "id": str(uuid.uuid5(NAMESPACE_DNS, "patient-1")),
        "name": fake.name(),
        "gender": "male",
        "birthDate": "1985-03-15",
        "identifier": f"PAT-{str(uuid.uuid5(NAMESPACE_DNS, 'patient-1'))[:8].upper()}"
    },
    {
        "id": str(uuid.uuid5(NAMESPACE_DNS, "patient-2")),
        "name": fake.name(),
        "gender": "female",
        "birthDate": "1990-07-22",
        "identifier": f"PAT-{str(uuid.uuid5(NAMESPACE_DNS, 'patient-2'))[:8].upper()}"
    },
    {
        "id": str(uuid.uuid5(NAMESPACE_DNS, "patient-3")),
        "name": fake.name(),
        "gender": "male",
        "birthDate": "1978-11-08",
        "identifier": f"PAT-{str(uuid.uuid5(NAMESPACE_DNS, 'patient-3'))[:8].upper()}"
    },
    {
        "id": str(uuid.uuid5(NAMESPACE_DNS, "patient-4")),
        "name": fake.name(),
        "gender": "female",
        "birthDate": "1965-01-30",
        "identifier": f"PAT-{str(uuid.uuid5(NAMESPACE_DNS, 'patient-4'))[:8].upper()}"
    },
    {
        "id": str(uuid.uuid5(NAMESPACE_DNS, "patient-5")),
        "name": fake.name(),
        "gender": "male",
        "birthDate": "1995-09-12",
        "identifier": f"PAT-{str(uuid.uuid5(NAMESPACE_DNS, 'patient-5'))[:8].upper()}"
    }
]

# Define 2 practitioners
PRACTITIONERS = [
    {
        "id": str(uuid.uuid5(NAMESPACE_DNS, "practitioner-1")),
        "name": "Dr. " + fake.last_name(),
        "specialty": "Cardiologie",
        "identifier": f"PRAC-{str(uuid.uuid5(NAMESPACE_DNS, 'practitioner-1'))[:8].upper()}"
    },
    {
        "id": str(uuid.uuid5(NAMESPACE_DNS, "practitioner-2")),
        "name": "Dr. " + fake.last_name(),
        "specialty": "Médecine Générale",
        "identifier": f"PRAC-{str(uuid.uuid5(NAMESPACE_DNS, 'practitioner-2'))[:8].upper()}"
    }
]

# Map patients to practitioners (3 for first, 2 for second)
PATIENT_PRACTITIONER_MAP = {
    PATIENTS[0]["id"]: PRACTITIONERS[0]["id"],
    PATIENTS[1]["id"]: PRACTITIONERS[0]["id"],
    PATIENTS[2]["id"]: PRACTITIONERS[0]["id"],
    PATIENTS[3]["id"]: PRACTITIONERS[1]["id"],
    PATIENTS[4]["id"]: PRACTITIONERS[1]["id"],
}


def get_patient_by_id(patient_id: str) -> dict:
    """Get patient data by ID"""
    for patient in PATIENTS:
        if patient["id"] == patient_id:
            return patient
    return None


def get_practitioner_for_patient(patient_id: str) -> dict:
    """Get the practitioner assigned to a patient"""
    practitioner_id = PATIENT_PRACTITIONER_MAP.get(patient_id)
    if practitioner_id:
        for practitioner in PRACTITIONERS:
            if practitioner["id"] == practitioner_id:
                return practitioner
    return None


if __name__ == "__main__":
    # Display patient and practitioner info for testing
    print("=" * 50)
    print("PATIENTS:")
    print("=" * 50)
    for p in PATIENTS:
        print(f"  - {p['name']} ({p['identifier']})")
    
    print("\n" + "=" * 50)
    print("PRACTITIONERS:")
    print("=" * 50)
    for pr in PRACTITIONERS:
        print(f"  - {pr['name']} - {pr['specialty']} ({pr['identifier']})")
