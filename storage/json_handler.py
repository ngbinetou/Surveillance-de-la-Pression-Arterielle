"""
JSON Handler for Normal Blood Pressure Data
Saves normal observations to local JSON files
"""
import json
import os
import sys
from datetime import datetime
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import STORAGE_CONFIG


class JSONHandler:
    """Handler for saving normal blood pressure observations to JSON files"""
    
    def __init__(self):
        """Initialize the JSON handler"""
        self.output_path = STORAGE_CONFIG["normal_data_path"]
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Create output directory if it doesn't exist"""
        # Get absolute path relative to project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.output_path = os.path.join(project_root, STORAGE_CONFIG["normal_data_path"])
        
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
            print(f"âœ“ Created output directory: {self.output_path}")
    
    def save_observation(self, observation: Dict, patient_id: str) -> str:
        """
        Save a normal observation to a JSON file.
        
        Args:
            observation: FHIR Observation resource
            patient_id: Patient identifier
        
        Returns:
            Path to the saved file
        """
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"observation_{patient_id[:8]}_{timestamp}.json"
        filepath = os.path.join(self.output_path, filename)
        
        # Add metadata to observation
        data = {
            "saved_at": datetime.now().isoformat(),
            "patient_id": patient_id,
            "status": "normal",
            "observation": observation
        }
        
        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    



