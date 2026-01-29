import json
import os
from datetime import datetime

from kafka import KafkaConsumer
from elasticsearch import Elasticsearch

import joblib


# 
# 1) CONFIG
# 

# Kafka
TOPIC = "blood_pressure_fhir"
KAFKA_BROKER = "localhost:9092"

# Elasticsearch
ES_URL = "http://localhost:9200"
ES_INDEX = "bp_anomalies"

# Dossier local pour stocker les cas normaux
OUT_DIR = os.path.join("data", "normal_cases")
os.makedirs(OUT_DIR, exist_ok=True)

# Connexion Elasticsearch
es = Elasticsearch(ES_URL)

# Charger le modèle ML entraîné (doit être à la racine du projet)
MODEL_PATH = "bp_logreg.joblib"
model = joblib.load(MODEL_PATH)
print(" Modèle ML chargé")


# 
# 2) OUTILS : EXTRACTION
# 

def extract_fields(obs: dict):
    """
    Extrait les champs utiles depuis une Observation FHIR (ton format producer).
    - patient_id : subject.reference = "Patient/<id>"
    - practitioner_id : performer[0].reference = "Practitioner/<id>" (si présent)
    - systolic / diastolic : component[0] / component[1]
    - timestamp : effectiveDateTime
    """
    # patient
    patient_ref = obs.get("subject", {}).get("reference", "Patient/unknown")
    patient_id = patient_ref.split("/")[-1]

    # practitioner (optionnel)
    performer = obs.get("performer", [])
    if performer and isinstance(performer, list):
        prac_ref = performer[0].get("reference", "Practitioner/unknown")
        practitioner_id = prac_ref.split("/")[-1]
    else:
        practitioner_id = "unknown"

    # pression
    components = obs.get("component", [])
    systolic = int(components[0]["valueQuantity"]["value"])
    diastolic = int(components[1]["valueQuantity"]["value"])

    # temps
    ts = obs.get("effectiveDateTime")

    return patient_id, practitioner_id, systolic, diastolic, ts


# 
# 3) OUTILS : RÈGLES + ML
# 

def classify_rules(sys_val: int, dia_val: int):
    """
    Règles simples (seuils du sujet):
    - systolique > 140 ou < 90
    - diastolique > 90 ou < 60

    Retour:
    - is_anomaly : bool
    - anomaly_type : "hypertension" / "hypotension" / "normal"
    - details : liste (tags précis)
    """
    details = []

    if sys_val > 140:
        details.append("hypertension_systolic")
    if sys_val < 90:
        details.append("hypotension_systolic")
    if dia_val > 90:
        details.append("hypertension_diastolic")
    if dia_val < 60:
        details.append("hypotension_diastolic")

    is_anomaly = len(details) > 0

    if not is_anomaly:
        anomaly_type = "normal"
    else:
        anomaly_type = "hypertension" if any("hyper" in d for d in details) else "hypotension"

    return is_anomaly, anomaly_type, details


def predict_risk_ml(sys_val: int, dia_val: int):
    """
    Prédiction ML très simple :
    - pred : 0 (normal) ou 1 (anormal)
    - risk : probabilité d'anomalie (entre 0 et 1)
    """
    X = [[sys_val, dia_val]]
    pred = int(model.predict(X)[0])
    risk = float(model.predict_proba(X)[0][1])
    return pred, risk


# 
# 4) STOCKAGE LOCAL / ES
# 

def save_normal_locally(obs: dict, patient_id: str, practitioner_id: str):
    """
    Sauvegarde 1 fichier JSON par mesure normale.
    Très simple à expliquer.
    """
    ts_file = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"{patient_id}_{practitioner_id}_{ts_file}.json"
    path = os.path.join(OUT_DIR, filename)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(obs, f, ensure_ascii=False, indent=2)


def index_anomaly_in_es(obs: dict, patient_id: str, practitioner_id: str,
                        sys_val: int, dia_val: int,
                        anomaly_type: str, details: list,
                        timestamp: str,
                        ml_pred: int, ml_risk: float):
    """
    Indexe les anomalies dans Elasticsearch.
    On ajoute ml_prediction et ml_risk_score pour la partie ML.
    """
    doc = {
        "patient_id": patient_id,
        "practitioner_id": practitioner_id,
        "systolic_pressure": sys_val,
        "diastolic_pressure": dia_val,
        "anomaly_type": anomaly_type,
        "anomaly_details": details,

        # Partie ML
        "ml_prediction": ml_pred,      # 0/1
        "ml_risk_score": ml_risk,      # 0..1

        # Temps (utile pour Kibana)
        "timestamp": timestamp,
        "@timestamp": timestamp,

        # Observation FHIR complète (debug)
        "fhir": obs,
    }

    es.index(index=ES_INDEX, document=doc)


# 
# 5) MAIN : KAFKA LOOP
# 

if __name__ == "__main__":
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        auto_offset_reset="latest",
        enable_auto_commit=True,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        group_id="bp-consumer",
    )

    print(" Consumer started (Ctrl+C pour arrêter)")

    for msg in consumer:
        obs = msg.value

        # 1) extraire
        patient_id, practitioner_id, sys_val, dia_val, ts = extract_fields(obs)

        # 2) règles (seuils)
        is_anomaly, anomaly_type, details = classify_rules(sys_val, dia_val)

        # 3) ML (toujours calculé, même si c’est normal)
        ml_pred, ml_risk = predict_risk_ml(sys_val, dia_val)

        # 4) stocker
        if is_anomaly:
            index_anomaly_in_es(
                obs, patient_id, practitioner_id,
                sys_val, dia_val,
                anomaly_type, details,
                ts,
                ml_pred, ml_risk
            )
            print(
                f"ANOMALY -> ES | patient={patient_id} prac={practitioner_id} "
                f"sys={sys_val} dia={dia_val} details={details} risk={ml_risk:.2f}"
            )
        else:
            save_normal_locally(obs, patient_id, practitioner_id)
            print(
                f"NORMAL -> LOCAL | patient={patient_id} prac={practitioner_id} "
                f"sys={sys_val} dia={dia_val} risk={ml_risk:.2f}"
            )
