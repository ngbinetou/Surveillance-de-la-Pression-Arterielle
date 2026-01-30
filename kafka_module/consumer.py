"""
Kafka Consumer for Blood Pressure FHIR Observations
Consumes observations, applies rules/ML, and routes to appropriate storage
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaConsumer
from kafka.errors import KafkaError

from datetime import datetime
from config.settings import KAFKA_CONFIG
from analysis.rules import BloodPressureAnalyzer
from storage.elasticsearch_handler import ElasticsearchHandler
from storage.json_handler import JSONHandler
from data_generator.patients import get_patient_by_id


class BloodPressureConsumer:
    """Kafka Consumer for processing blood pressure observations"""
    
    def __init__(self, use_ml: bool = False):
        """
        Initialize the Kafka consumer.
        
        Args:
            use_ml: Whether to use ML model for classification (optional)
        """
        self.topic = KAFKA_CONFIG["topic"]
        self.consumer = None
        self.use_ml = use_ml
        
        # Initialize components
        self.analyzer = BloodPressureAnalyzer(use_ml=use_ml)
        self.es_handler = ElasticsearchHandler()
        self.json_handler = JSONHandler()
        
        self._connect()
    
    def _connect(self):
        """Establish connection to Kafka broker"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=KAFKA_CONFIG["bootstrap_servers"],
                group_id=KAFKA_CONFIG["group_id"],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                auto_offset_reset='latest',
                enable_auto_commit=True
            )
            print(f"[OK] Connected to Kafka and subscribed to '{self.topic}'")
        except KafkaError as e:
            print(f"[ERROR] Failed to connect to Kafka: {e}")
            raise
    
    def process_observation(self, observation: dict, patient_id: str):
        """
        Process a single observation: analyze and route to appropriate storage.
        
        Args:
            observation: FHIR Observation resource
            patient_id: Patient identifier
        """
        # Analyze the observation
        analysis_result = self.analyzer.analyze(observation)
        
        systolic = analysis_result["systolic"]
        diastolic = analysis_result["diastolic"]
        is_normal = analysis_result["is_normal"]
        anomaly_details = analysis_result.get("anomaly_details", {})
        
        if is_normal:
            # Store in local JSON file
            self.json_handler.save_observation(observation, patient_id)
            print(f"[OK] NORMAL | Patient {patient_id[:8]}... | "
                  f"BP: {systolic}/{diastolic} mmHg -> Saved to JSON")
        else:
            # Index in Elasticsearch
            anomaly_type = anomaly_details.get("type", "unknown")
            # Enrich with patient details
            patient = get_patient_by_id(patient_id)
            patient_details = {}
            
            if patient:
                birth_date = datetime.strptime(patient["birthDate"], "%Y-%m-%d")
                today = datetime.now()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                
                # Determine age range
                if age <= 18:
                    age_range = "0-18"
                elif age <= 35:
                    age_range = "19-35"
                elif age <= 50:
                    age_range = "36-50"
                elif age <= 65:
                    age_range = "51-65"
                else:
                    age_range = "65+"
                
                # Translate Sex to French
                sex_fr = "Homme" if patient["gender"] == "male" else "Femme" if patient["gender"] == "female" else patient["gender"]

                patient_details = {
                    "sex": sex_fr,
                    "age": age,
                    "age_range": age_range
                }

            self.es_handler.index_abnormal_observation(
                observation,
                patient_id,
                anomaly_details,
                patient_details
            )
            print(f"[DEBUG] Indexing anomaly: {anomaly_details}")
            print(f"[ALERT] | Patient {patient_id[:8]}... | "
                  f"BP: {systolic}/{diastolic} mmHg | "
                  f"Type: {anomaly_type} -> Indexed in Elasticsearch")
    
    def run(self):
        """
        Start consuming messages from Kafka topic.
        Processes each message and routes to appropriate storage.
        """
        print("\n" + "=" * 60)
        print("Starting Blood Pressure Consumer...")
        print(f"Listening to topic: {self.topic}")
        print(f"ML Model: {'Enabled' if self.use_ml else 'Disabled (using rules only)'}")
        print("=" * 60 + "\n")
        print("Press Ctrl+C to stop\n")
        
        try:
            for message in self.consumer:
                observation = message.value
                patient_id = message.key
                
                self.process_observation(observation, patient_id)
                
        except KeyboardInterrupt:
            print("\n\n[OK] Consumer stopped by user")
        finally:
            self.close()
    
    def close(self):
        """Close all connections"""
        if self.consumer:
            self.consumer.close()
            print("[OK] Kafka consumer connection closed")
        self.es_handler.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Blood Pressure Monitoring System - Consumer")
    parser.add_argument(
        "--ml",
        action="store_true",
        help="Enable ML model for blood pressure classification (requires trained model)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Blood Pressure Monitoring System - Consumer")
    print("=" * 60)
    print(f"\nClassification mode: {'ML Model' if args.ml else 'Rules-based'}")
    print("Consuming observations from Kafka and routing to storage...\n")
    
    try:
        consumer = BloodPressureConsumer(use_ml=args.ml)
        consumer.run()
    except KeyboardInterrupt:
        print("\nConsumer stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Docker containers are running:")
        print("  docker-compose up -d")
