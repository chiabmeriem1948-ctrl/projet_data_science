# Système de surveillance de la pression artérielle  
(Kafka + Elasticsearch + Kibana + Machine Learning)

Ce projet met en place un pipeline de data engineering et data science en temps réel
pour la surveillance de la pression artérielle à partir de données médicales au format FHIR.
Il combine des règles cliniques simples et un modèle de machine learning afin de détecter
des anomalies et d’estimer un score de risque.

---

## Objectifs du projet
- Générer des données de pression artérielle en temps réel
- Détecter automatiquement les anomalies (hypertension / hypotension)
- Estimer un score de risque à l’aide d’un modèle de Machine Learning
- Visualiser les résultats dans Kibana
- Mettre en place des alertes automatiques
- Stocker les cas normaux localement

---

## Architecture du système

1. **Producer (Python)**  
   Génère des observations de pression artérielle (systolique / diastolique)
   au format FHIR et les envoie dans Kafka.

2. **Kafka**  
   Sert de système de messagerie pour le transport des données en temps réel.

3. **Consumer (Python)**  
   - Consomme les messages Kafka  
   - Extrait les informations importantes (patient, valeurs, timestamp)  
   - Détecte les anomalies à l’aide de seuils cliniques  
   - Calcule un score de risque ML (régression logistique)  
   - Indexe les anomalies dans Elasticsearch  
   - Stocke les cas normaux localement au format JSON  

4. **Elasticsearch**  
   Stocke les événements anormaux pour l’analyse et la visualisation.

5. **Kibana**  
   Permet la création de dashboards et d’alertes en temps réel.

---

## Prérequis
- Docker
- Docker Compose
- Python 3.10 ou plus
- Navigateur web

---

## Installation et lancement du projet

### 1. Cloner le dépôt
```bash
git clone https://github.com/chiabmeriem1948-ctrl/projet_data_science.git
cd projet_data_science

