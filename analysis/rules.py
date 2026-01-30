"""
Blood Pressure Analysis Rules
Classifies observations as normal or abnormal based on medical thresholds
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import BP_THRESHOLDS
from typing import Dict, Tuple


class BloodPressureAnalyzer:
    """
    Analyzer for blood pressure observations.
    Uses rule-based classification with optional ML model support.
    """
    
    def __init__(self, use_ml: bool = False):
        """
        Initialize the analyzer.
        
        Args:
            use_ml: Whether to use ML model for classification
        """
        self.use_ml = use_ml
        self.ml_model = None
        
        # Force load ML model regardless of flag, as it is now required
        self._load_ml_model()
    
    def _load_ml_model(self):
        """Load the trained ML model if available"""
        try:
            from analysis.ml_model import BloodPressureMLModel
            self.ml_model = BloodPressureMLModel()
            self.ml_model.load_model()
            print("âœ“ ML model loaded successfully")
        except Exception as e:
            print(f"âš  Could not load ML model: {e}")
            print("  Falling back to rule-based classification")
            self.use_ml = False
    
    def extract_values(self, observation: dict) -> Tuple[int, int]:
        """
        Extract systolic and diastolic values from FHIR observation.
        
        Args:
            observation: FHIR Observation resource
        
        Returns:
            Tuple of (systolic, diastolic) values
        """
        components = observation.get("component", [])
        
        systolic = None
        diastolic = None
        
        for component in components:
            code = component.get("code", {}).get("coding", [{}])[0].get("code", "")
            value = component.get("valueQuantity", {}).get("value")
            
            if code == "8480-6":  # LOINC code for systolic
                systolic = value
            elif code == "8462-4":  # LOINC code for diastolic
                diastolic = value
        
        return systolic, diastolic
    
    def classify_by_rules(self, systolic: int, diastolic: int) -> Dict:
        """
        Classify blood pressure using rule-based thresholds.
        
        Args:
            systolic: Systolic blood pressure in mmHg
            diastolic: Diastolic blood pressure in mmHg
        
        Returns:
            Classification result with anomaly details
        """
        anomalies = []
        alert_types = []
        
        # Check systolic
        if systolic < BP_THRESHOLDS["systolic"]["min"]:
            alert = "Systolic Low"
            alert_types.append(alert)
            anomalies.append({
                "component": "systolic",
                "type": alert,
                "value": systolic,
                "threshold": BP_THRESHOLDS["systolic"]["min"],
                "message": f"Systolic BP too low: {systolic} < {BP_THRESHOLDS['systolic']['min']} mmHg"
            })
        elif systolic > BP_THRESHOLDS["systolic"]["max"]:
            alert = "Systolic High"
            alert_types.append(alert)
            anomalies.append({
                "component": "systolic",
                "type": alert,
                "value": systolic,
                "threshold": BP_THRESHOLDS["systolic"]["max"],
                "message": f"Systolic BP too high: {systolic} > {BP_THRESHOLDS['systolic']['max']} mmHg"
            })
        
        # Check diastolic
        if diastolic < BP_THRESHOLDS["diastolic"]["min"]:
            alert = "Diastolic Low"
            alert_types.append(alert)
            anomalies.append({
                "component": "diastolic",
                "type": alert,
                "value": diastolic,
                "threshold": BP_THRESHOLDS["diastolic"]["min"],
                "message": f"Diastolic BP too low: {diastolic} < {BP_THRESHOLDS['diastolic']['min']} mmHg"
            })
        elif diastolic > BP_THRESHOLDS["diastolic"]["max"]:
            alert = "Diastolic High"
            alert_types.append(alert)
            anomalies.append({
                "component": "diastolic",
                "type": alert,
                "value": diastolic,
                "threshold": BP_THRESHOLDS["diastolic"]["max"],
                "message": f"Diastolic BP too high: {diastolic} > {BP_THRESHOLDS['diastolic']['max']} mmHg"
            })
        
        is_normal = len(anomalies) == 0
        
        result = {
            "is_normal": is_normal,
            "anomaly_details": {}
        }
        
        if not is_normal:
            result["anomaly_details"] = {
                "type": ", ".join(alert_types), # Combined string for legacy support if needed
                "alert_types": alert_types,     # List of specific alerts
                "anomalies": anomalies,
                "severity": "high" if len(anomalies) > 1 else "medium"
            }
        
        return result
    
    def analyze(self, observation: dict) -> Dict:
        """
        Analyze a blood pressure observation.
        
        Args:
            observation: FHIR Observation resource
        
        Returns:
            Analysis result including classification
        """
        systolic, diastolic = self.extract_values(observation)
        
        if systolic is None or diastolic is None:
            raise ValueError("Could not extract blood pressure values from observation")
        
        # ALWAYS use ML model as requested
        if not self.ml_model:
            # Try to load it if not loaded (though __init__ should have handled it)
            self._load_ml_model()
            
        if self.ml_model:
            result = self.ml_model.predict(systolic, diastolic)
        else:
            raise RuntimeError("ML Model is required but could not be loaded.")
        
        # Add values to result
        result["systolic"] = systolic
        result["diastolic"] = diastolic
        result["observation_id"] = observation.get("id")
        result["patient_ref"] = observation.get("subject", {}).get("reference")
        
        return result


if __name__ == "__main__":
    # Test the analyzer
    print("=" * 60)
    print("Testing Blood Pressure Analyzer")
    print("=" * 60)
    
    analyzer = BloodPressureAnalyzer(use_ml=False)
    
    # Test cases
    test_cases = [
        (120, 80, "Normal"),
        (145, 95, "Hypertension"),
        (85, 55, "Hypotension"),
        (150, 50, "Mixed (high systolic, low diastolic)")
    ]
    
    for systolic, diastolic, expected in test_cases:
        result = analyzer.classify_by_rules(systolic, diastolic)
        status = "Normal" if result["is_normal"] else result["anomaly_details"]["type"]
        print(f"\nBP: {systolic}/{diastolic} mmHg")
        print(f"  Expected: {expected}")
        print(f"  Result: {status}")
        if not result["is_normal"]:
            for anomaly in result["anomaly_details"]["anomalies"]:
                print(f"    - {anomaly['message']}")

