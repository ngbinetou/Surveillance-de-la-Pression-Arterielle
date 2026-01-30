"""
Elasticsearch Handler for Abnormal Blood Pressure Data
Indexes abnormal observations for visualization in Kibana
"""
import json
import sys
import os
from datetime import datetime
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError

from config.settings import ELASTICSEARCH_CONFIG


class ElasticsearchHandler:
    """Handler for indexing abnormal blood pressure data in Elasticsearch"""
    
    def __init__(self):
        """Initialize the Elasticsearch client"""
        self.index_name = ELASTICSEARCH_CONFIG["index_name"]
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Elasticsearch"""
        try:
            self.client = Elasticsearch(
                ELASTICSEARCH_CONFIG["hosts"],
                verify_certs=False,
                ssl_show_warn=False
            )
            
            # Check connection
            if self.client.ping():
                print(f"[OK] Connected to Elasticsearch at {ELASTICSEARCH_CONFIG['hosts']}")
                self._create_index_if_not_exists()
            else:
                print("[WARN] Could not connect to Elasticsearch (will retry on use)")
                
        except ESConnectionError as e:
            print(f"[WARN] Elasticsearch connection failed: {e}")
            print("  Data will be queued and indexed when connection is available")
    
    def _create_index_if_not_exists(self):
        """Create the index with appropriate mappings if it doesn't exist"""
        if not self.client.indices.exists(index=self.index_name):
            mapping = {
                "mappings": {
                    "properties": {
                        "observation_id": {"type": "keyword"},
                        "patient_id": {"type": "keyword"},
                        "patient_reference": {"type": "keyword"},
                        "practitioner_reference": {"type": "keyword"},
                        "systolic_pressure": {"type": "integer"},
                        "diastolic_pressure": {"type": "integer"},
                        "anomaly_type": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "severity": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "indexed_at": {"type": "date"},
                        "patient_sex": {"type": "keyword"},
                        "patient_age": {"type": "integer"},
                        "patient_age_range": {"type": "keyword"},
                        "fhir_observation": {"type": "object", "enabled": False}
                    }
                }
            }
            
            self.client.indices.create(index=self.index_name, body=mapping)
            print(f"[OK] Created Elasticsearch index: {self.index_name}")
    
    def index_abnormal_observation(
        self,
        observation: dict,
        patient_id: str,
        anomaly_details: Dict,
        patient_details: Dict = None
    ):
        """
        Index an abnormal blood pressure observation.
        
        Args:
            observation: FHIR Observation resource
            patient_id: Patient identifier
            anomaly_details: Details about the anomaly detected
            patient_details: Optional demographic details (age, sex, etc.)
        """
        if self.client is None:
            print("[WARN] Elasticsearch not connected, skipping indexing")
            return
        
        # Extract values from observation
        components = observation.get("component", [])
        systolic = None
        diastolic = None
        
        for component in components:
            code = component.get("code", {}).get("coding", [{}])[0].get("code", "")
            value = component.get("valueQuantity", {}).get("value")
            
            if code == "8480-6":
                systolic = value
            elif code == "8462-4":
                diastolic = value
        
        # Prepare document for indexing
        doc = {
            "observation_id": observation.get("id"),
            "patient_id": patient_id,
            "patient_reference": observation.get("subject", {}).get("reference"),
            "practitioner_reference": observation.get("performer", [{}])[0].get("reference", "").replace("Practitioner/", "Praticien "),
            "systolic_pressure": systolic,
            "diastolic_pressure": diastolic,
            "anomaly_type": anomaly_details.get("type", "unknown"),
            "alert_types": anomaly_details.get("alert_types", []),
            "severity": anomaly_details.get("severity", "medium"),
            "timestamp": observation.get("effectiveDateTime"),
            "indexed_at": datetime.now().isoformat(),
            "fhir_observation": observation
        }
        
        if patient_details:
            doc["patient_sex"] = patient_details.get("sex")
            doc["patient_age"] = patient_details.get("age")
            doc["patient_age_range"] = patient_details.get("age_range")
        
        try:
            response = self.client.index(
                index=self.index_name,
                document=doc
            )
            return response
            
        except Exception as e:
            print(f"[ERROR] Failed to index observation: {e}")
            return None
    
    def search_by_patient(self, patient_id: str, size: int = 100) -> list:
        """
        Search for abnormal observations by patient ID.
        
        Args:
            patient_id: Patient identifier
            size: Maximum number of results
        
        Returns:
            List of matching documents
        """
        if self.client is None:
            return []
        
        query = {
            "query": {
                "term": {"patient_id": patient_id}
            },
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": size
        }
        
        response = self.client.search(index=self.index_name, body=query)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    def search_by_anomaly_type(self, anomaly_type: str, size: int = 100) -> list:
        """
        Search for observations by anomaly type.
        
        Args:
            anomaly_type: Type of anomaly ("hypertension" or "hypotension")
            size: Maximum number of results
        
        Returns:
            List of matching documents
        """
        if self.client is None:
            return []
        
        query = {
            "query": {
                "term": {"anomaly_type": anomaly_type}
            },
            "sort": [{"timestamp": {"order": "desc"}}],
            "size": size
        }
        
        response = self.client.search(index=self.index_name, body=query)
        return [hit["_source"] for hit in response["hits"]["hits"]]
    
    def get_statistics(self) -> Dict:
        """Get aggregated statistics on abnormal observations"""
        if self.client is None:
            return {}
        
        query = {
            "size": 0,
            "aggs": {
                "by_anomaly_type": {
                    "terms": {"field": "anomaly_type"}
                },
                "by_severity": {
                    "terms": {"field": "severity"}
                },
                "avg_systolic": {
                    "avg": {"field": "systolic_pressure"}
                },
                "avg_diastolic": {
                    "avg": {"field": "diastolic_pressure"}
                }
            }
        }
        
        response = self.client.search(index=self.index_name, body=query)
        return response["aggregations"]
    
    def close(self):
        """Close the Elasticsearch connection"""
        if self.client:
            self.client.close()
            print("[OK] Elasticsearch connection closed")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Elasticsearch Handler")
    print("=" * 60)
    
    handler = ElasticsearchHandler()
    
    # Create a test observation
    test_observation = {
        "id": "test-123",
        "subject": {"reference": "Patient/pat-001"},
        "performer": [{"reference": "Practitioner/prac-001"}],
        "effectiveDateTime": datetime.now().isoformat(),
        "component": [
            {
                "code": {"coding": [{"code": "8480-6"}]},
                "valueQuantity": {"value": 155}
            },
            {
                "code": {"coding": [{"code": "8462-4"}]},
                "valueQuantity": {"value": 95}
            }
        ]
    }
    
    test_anomaly = {
        "type": "hypertension",
        "severity": "high",
        "anomalies": [{"message": "Systolic BP too high: 155 > 140 mmHg"}]
    }
    
    result = handler.index_abnormal_observation(
        test_observation,
        "pat-001",
        test_anomaly
    )
    
    if result:
        print(f"[OK] Test observation indexed successfully")
    
    handler.close()
