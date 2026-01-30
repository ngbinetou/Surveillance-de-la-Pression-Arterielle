"""
Kafka Producer for Blood Pressure FHIR Observations
Publishes blood pressure measurements to Kafka topic in real-time
"""
import json
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaProducer
from kafka.errors import KafkaError

from config.settings import KAFKA_CONFIG, GENERATION_CONFIG
from data_generator.patients import PATIENTS
from data_generator.fhir_generator import generate_observation_for_patient


class BloodPressureProducer:
    """Kafka Producer for publishing blood pressure observations"""
    
    def __init__(self):
        """Initialize the Kafka producer"""
        self.topic = KAFKA_CONFIG["topic"]
        self.producer = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Kafka broker"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=KAFKA_CONFIG["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3
            )
            print(f"[OK] Connected to Kafka broker at {KAFKA_CONFIG['bootstrap_servers']}")
        except KafkaError as e:
            print(f"[ERROR] Failed to connect to Kafka: {e}")
            raise
    
    def send_observation(self, observation: dict, patient_id: str):
        """
        Send a single observation to Kafka topic.
        
        Args:
            observation: FHIR Observation resource
            patient_id: Patient identifier (used as message key)
        """
        try:
            future = self.producer.send(
                self.topic,
                key=patient_id,
                value=observation
            )
            # Wait for the message to be delivered
            record_metadata = future.get(timeout=10)
            
            # Extract blood pressure values for logging
            systolic = observation["component"][0]["valueQuantity"]["value"]
            diastolic = observation["component"][1]["valueQuantity"]["value"]
            
            print(f"[OK] Sent: Patient {patient_id[:8]}... | "
                  f"BP: {systolic}/{diastolic} mmHg | "
                  f"Partition: {record_metadata.partition}")
            
        except KafkaError as e:
            print(f"[ERROR] Failed to send observation: {e}")
    
    def run_continuous(self, interval_seconds: int = None):
        """
        Continuously generate and send observations for all patients.
        
        Args:
            interval_seconds: Time between observation batches (default from config)
        """
        if interval_seconds is None:
            interval_seconds = GENERATION_CONFIG["interval_seconds"]
        
        print("\n" + "=" * 60)
        print("Starting continuous blood pressure monitoring...")
        print(f"Publishing to topic: {self.topic}")
        print(f"Interval: Every {interval_seconds} seconds")
        print(f"Patients: {len(PATIENTS)}")
        print("=" * 60 + "\n")
        print("Press Ctrl+C to stop\n")
        
        try:
            batch_count = 0
            while True:
                batch_count += 1
                print(f"\n--- Batch #{batch_count} - {time.strftime('%H:%M:%S')} ---")
                
                for patient in PATIENTS:
                    observation = generate_observation_for_patient(
                        patient["id"],
                        simulate_anomaly=True
                    )
                    self.send_observation(observation, patient["id"])
                
                self.producer.flush()
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n[OK] Producer stopped by user")
        finally:
            self.close()
    
    def close(self):
        """Close the Kafka producer connection"""
        if self.producer:
            self.producer.close()
            print("[OK] Kafka producer connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("Blood Pressure Monitoring System - Producer")
    print("=" * 60)
    print("\nStarting FHIR observation generator...")
    print("Observations will be published to Kafka in real-time.\n")
    
    try:
        producer = BloodPressureProducer()
        producer.run_continuous()
    except KeyboardInterrupt:
        print("\nProducer stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure Docker containers are running:")
        print("  docker-compose up -d")
