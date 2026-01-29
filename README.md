#  Système de surveillance de la pression artérielle  
Kafka + Elasticsearch + Kibana + Machine Learning

Projet de data engineering / data science mettant en place un pipeline temps réel de surveillance de la pression artérielle à partir de données simulées au format FHIR.

---

##  Objectifs du projet
- Simuler un flux temps réel de données médicales (pression artérielle)
- Détecter automatiquement des anomalies (hypertension / hypotension)
- Estimer un score de risque via un modèle de Machine Learning
- Visualiser les résultats dans Kibana
- Mettre en place des alertes temps réel

---

##  Architecture du système

1. Producer (Python)  
   Génère des données de pression artérielle au format FHIR et les envoie vers Kafka.

2. Kafka  
   Sert de système de streaming pour transporter les données en temps réel.

3. Consumer (Python)  
   - Consomme les messages Kafka  
   - Extrait les champs utiles (patient, systolique, diastolique, timestamp)  
   - Détecte les anomalies avec des règles cliniques  
   - Calcule un score de risque ML (régression logistique)  
   - Indexe les anomalies dans Elasticsearch  
   - Stocke les cas normaux en local (fichiers JSON)

4. Elasticsearch  
   Stockage et indexation des anomalies détectées.

5. Kibana  
   Visualisation des données, dashboards et alertes temps réel.

---

##  Technologies utilisées
- Python 3
- Kafka
- Docker & Docker Compose
- Elasticsearch
- Kibana
- Scikit-learn
- Joblib
- NumPy

---

##  Structure du projet

projet_data_science/
├── producer/
│   └── producer.py
├── consumer/
│   ├── consumer.py
│   └── data/
│       └── normal_cases/
├── train_ml.py
├── docker-compose.yml
├── .gitignore
└── README.md

---

##  Lancement du projet

### 1 Démarrer l’infrastructure
docker compose up -d

- Elasticsearch : http://localhost:9200  
- Kibana : http://localhost:5601  

---

### 2 Installer les dépendances Python
pip install kafka-python elasticsearch numpy scikit-learn joblib

---

### 3 Entraîner le modèle ML
python train_ml.py

---

### 4 Lancer le consumer
python consumer/consumer.py

---

### 5 Lancer le producer
python producer/producer.py

---

##  Dashboards Kibana
Accès :
Kibana → Analytics → Dashboard

Dashboards réalisés :
- Répartition des types d’anomalies
- Évolution temporelle des anomalies
- Cas critiques récents
- Distribution des scores de risque ML
- Évolution du risque ML au cours du temps

---

##  Alertes Kibana
Des règles d’alertes ont été créées pour :
- Hypertension systolique
- Hypertension diastolique
- Cas critiques combinés
- Pics anormaux d’événements

Accès :
Kibana → Stack Management → Rules

---

##  Stockage des cas normaux
Les mesures normales sont stockées localement sous forme de fichiers JSON dans :
consumer/data/normal_cases/

Ces fichiers ne sont pas versionnés sur GitHub (présents dans le .gitignore).



##  Conclusion
Ce projet illustre une chaîne complète de data engineering et data science incluant ingestion temps réel, règles métiers, machine learning, visualisation et alerting.
