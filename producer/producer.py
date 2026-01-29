import json
import time
from datetime import datetime, timezone
from faker import Faker
from kafka import KafkaProducer

# Générateur de valeurs réalistes
fake = Faker()

# Kafka
KAFKA_BROKER = "localhost:9092"
TOPIC = "blood_pressure_fhir"

# 5 patients fixes 
PATIENT_IDS = ["PAT-001", "PAT-002", "PAT-003", "PAT-004", "PAT-005"]

# 2 practitioners fixes (soignants)
PRACTITIONER_IDS = ["PRAC-01", "PRAC-02"]

# Producteur Kafka : envoie des dict Python encodés en JSON
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

def now_iso():
    """Renvoie la date/heure actuelle en ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).isoformat()

def build_fhir_observation(patient_id: str, practitioner_id: str) -> dict:
    """
    Crée une Observation FHIR (format simple).
    On inclut :
    - subject : Patient/...
    - performer : Practitioner/...
    - component : systolic + diastolic
    """
    systolic = fake.random_int(min=80, max=190)
    diastolic = fake.random_int(min=50, max=120)

    return {
        "resourceType": "Observation",
        "status": "final",
        "subject": {"reference": f"Patient/{patient_id}"},
        "performer": [{"reference": f"Practitioner/{practitioner_id}"}],
        "effectiveDateTime": now_iso(),
        "component": [
            {
                "code": {"text": "Systolic Blood Pressure"},
                "valueQuantity": {"value": systolic, "unit": "mmHg"},
            },
            {
                "code": {"text": "Diastolic Blood Pressure"},
                "valueQuantity": {"value": diastolic, "unit": "mmHg"},
            },
        ],
    }

if __name__ == "__main__":
    print("Producer started (5 patients / 2 practitioners / every 5 seconds)")
    idx = 0

    # Boucle infinie : toutes les 5 secondes, on envoie 5 messages (1 par patient)
    while True:
        for patient_id in PATIENT_IDS:
            # On alterne PRAC-01 / PRAC-02
            practitioner_id = PRACTITIONER_IDS[idx % len(PRACTITIONER_IDS)]
            idx += 1

            obs = build_fhir_observation(patient_id, practitioner_id)

            # Envoi vers Kafka
            producer.send(TOPIC, obs)
            print(f"Sent -> patient={patient_id} practitioner={practitioner_id}")

        # On force l’envoi immédiat du batch
        producer.flush()

        # Pause de 5 secondes 
        time.sleep(5)
