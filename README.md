# Système de Surveillance des Données de Pression Artérielle

## Description

Ce système de surveillance en temps réel utilise une architecture de streaming moderne pour traiter des données physiologiques standardisées. Il permet la détection proactive d'anomalies de pression artérielle via une classification hybride (Règles métiers + Machine Learning).

### Stack Technique
- **Standard Santé** : FHIR (Fast Healthcare Interoperability Resources) R4, Codes LOINC.
- **Streaming** : Apache Kafka (Zookeeper/Broker).
- **Indexation** : Elasticsearch 8.11.
- **Visualisation** : Kibana (Dashboards interactifs).
- **IA/ML** : Scikit-learn (Random Forest Classifier).
- **Backend** : Python 3.9+ (kafka-python, fhir.resources).

## Architecture

Le flux de données suit un pipeline robuste :
1.  **Générateur** : Produit des observations FHIR réalistes avec horodatage et métadonnées patients.
2.  **Kafka Broker** : Assure le transport fiable des messages avec partitionnement par ID patient.
3.  **Consumer** : Analyse chaque message via l'analyseur hybride.
4.  **Stockage Dual** :
    *   **Elasticsearch** : Indexation immédiate des anomalies pour alertes.
    *   **JSON Local** : Archivage structuré des données normales pour audit.
5.  **Dashboards** : Monitoring en temps réel via Kibana.

## Installation

### Prérequis
- Docker Desktop
- Python 3.9+

### Configuration
1. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```
2. **Lancer l'infrastructure** :
   ```bash
   docker-compose up -d
   ```

## Utilisation

### 1. Préparation du Modèle ML
Le système requiert un modèle entraîné pour fonctionner de manière optimale.
```bash
python -m analysis.ml_model
```

### 2. Lancement du Pipeline
Lancer le consommateur (analyseur) puis le producteur (générateur) dans deux terminaux séparés :

**Terminal 1 (Consumer)** :
```bash
python -m kafka_module.consumer --ml
```

**Terminal 2 (Producer)** :
```bash
python -m kafka_module.producer
```

## Machine Learning

Le système utilise un classifieur **Random Forest** entraîné sur les seuils cliniques définis dans `config/settings.py`.

- **Seuils Systoliques** : 90 - 140 mmHg
- **Seuils Diastoliques** : 60 - 90 mmHg

Le modèle analyse non seulement les valeurs brutes mais aussi les corrélations pour assigner une **probabilité de confiance** à chaque alerte.

### Mode de classification
- **Défaut** : Classification ML active.
- **Optionnel** : Utiliser `--no-ml` pour basculer sur une classification strictement basée sur les règles statiques.

## Dashboard Kibana

Le projet inclut un dashboard Kibana offrant une visibilité à 360° sur la santé des patients.



### Indicateurs clés :
### Indicateurs clés :
- **KPIs** : Anomalies Totales, Nombre de Patients Impactés, Moyenne Systolique, Moyenne Diastolique.
- **Temporel** : 
    - Anomalies dans le Temps (Évolution du volume d'alertes).
    - Évolution Pression Moyenne (Tendances physiologiques).
- **Analyse des Anomalies** : 
    - Anomalies par Gravité (High vs Medium).
    - Répartition par Sévérité (Graphique sectoriel "Donut").
    - Types d'Alertes (Systolic High/Low, Diastolic High/Low).
- **Démographie & Contexte** : 
    - Répartition par Sexe (Male/Female).
    - Anomalies par Age (Histogramme par tranches d'âge).
    - Alertes par Praticien.
    - Alertes par Patient.
- **Tableau de bord** : Dernières Anomalies (Liste détaillée avec horodatage et patient).

## Structure du Projet

```
Projet/
├── analysis/           # Cœur de l'intelligence (Rules & ML Model)
├── config/             # Paramètres Kafka, ES et seuils médicaux
├── data_generator/     # Simulation FHIR-compliant (Patients & Observations)
├── kafka_module/       # Implémentation Producer/Consumer Kafka
├── models/             # Modèles sérialisés (.pkl)
├── storage/            # Gestionnaires de persistance (ES & JSON)
├── output/             # Historique des données normales
├── docker-compose.yml  # Infrastructure Dockerisée
└── requirements.txt    # Dépendances du projet
```


