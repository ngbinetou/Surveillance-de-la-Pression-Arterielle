"""
Machine Learning Model for Blood Pressure Classification
Uses supervised learning to classify blood pressure as normal or abnormal
"""
import os
import sys
import numpy as np
import pandas as pd
from typing import Dict, Tuple

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib 

from config.settings import STORAGE_CONFIG, BP_THRESHOLDS


class BloodPressureMLModel:
    """
    Machine Learning model for blood pressure classification.
    Trained on synthetic data using clinical thresholds as labels.
    """
    
    def __init__(self):
        """
        Initialize the ML model.
        """
        self.model_type = "random_forest"
        self.model_path = STORAGE_CONFIG["model_path"]
        
        # Initialize Random Forest model
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
    

    def generate_training_data(self, n_samples: int = 10000) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        Generate synthetic training data based on clinical thresholds.
        
        Args:
            n_samples: Number of samples to generate
        
        Returns:
            Tuple of (features DataFrame, labels array)
        """
        np.random.seed(42)
        
        # Generate balanced dataset (50% normal, 50% abnormal)
        n_normal = n_samples // 2
        n_abnormal = n_samples - n_normal
        
        # Generate Normal Data
        systolic_normal = np.random.randint(
            BP_THRESHOLDS["systolic"]["min"], 
            BP_THRESHOLDS["systolic"]["max"] + 1, 
            n_normal
        )
        diastolic_normal = np.random.randint(
            BP_THRESHOLDS["diastolic"]["min"], 
            BP_THRESHOLDS["diastolic"]["max"] + 1, 
            n_normal
        )
        labels_normal = np.zeros(n_normal)
        
        # Generate Abnormal Data
        # We'll generate random values and filter for abnormal ones to ensure they are truly abnormal
        systolic_abnormal = []
        diastolic_abnormal = []
        
        while len(systolic_abnormal) < n_abnormal:
            # Generate batch of random values in wider range
            s_batch = np.random.randint(60, 200, n_abnormal)
            d_batch = np.random.randint(40, 130, n_abnormal)
            
            for s, d in zip(s_batch, d_batch):
                is_s_normal = BP_THRESHOLDS["systolic"]["min"] <= s <= BP_THRESHOLDS["systolic"]["max"]
                is_d_normal = BP_THRESHOLDS["diastolic"]["min"] <= d <= BP_THRESHOLDS["diastolic"]["max"]
                
                if not (is_s_normal and is_d_normal):
                    systolic_abnormal.append(s)
                    diastolic_abnormal.append(d)
                    if len(systolic_abnormal) == n_abnormal:
                        break
        
        labels_abnormal = np.ones(n_abnormal)
        
        # Combine and shuffle
        systolic = np.concatenate([systolic_normal, systolic_abnormal])
        diastolic = np.concatenate([diastolic_normal, diastolic_abnormal])
        labels = np.concatenate([labels_normal, labels_abnormal])
        
        # Shuffle indices
        indices = np.arange(n_samples)
        np.random.shuffle(indices)
        
        features = pd.DataFrame({
            "systolic": systolic[indices],
            "diastolic": diastolic[indices]
        })
        
        return features, labels[indices]
    
    def train(self, n_samples: int = 10000):
        """
        Train the model on synthetic data.
        
        Args:
            n_samples: Number of samples to use for training
        """
        print("Generating training data...")
        X, y = self.generate_training_data(n_samples)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"Training {self.model_type} model...")
        print(f"  Training samples: {len(X_train)}")
        print(f"  Test samples: {len(X_test)}")
        
        # Train
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\nModel Performance:")
        print(f"  Accuracy: {accuracy:.2%}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=["Normal", "Abnormal"]))
        
        return accuracy
    
    def save_model(self):
        """Save the trained model to disk"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        
        joblib.dump(self.model, self.model_path)
        print(f"âœ“ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load a pre-trained model from disk"""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"âœ“ Model loaded from {self.model_path}")
        else:
            raise FileNotFoundError(f"Model not found at {self.model_path}")
    
    def predict(self, systolic: int, diastolic: int) -> Dict:
        """
        Predict if blood pressure is normal or abnormal.
        
        Args:
            systolic: Systolic blood pressure in mmHg
            diastolic: Diastolic blood pressure in mmHg
        
        Returns:
            Prediction result with probability
        """
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        X = pd.DataFrame({"systolic": [systolic], "diastolic": [diastolic]})
        
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]
        
        is_normal = prediction == 0
        confidence = probabilities[int(prediction)]
        
        result = {
            "is_normal": is_normal,
            "confidence": float(confidence),
            "method": "ml_model",
            "model_type": self.model_type
        }
        
        if not is_normal:
            # Determine anomaly type based on thresholds (post-prediction detailed analysis)
            alert_types = []
            
            # Check systolic
            if systolic < BP_THRESHOLDS["systolic"]["min"]:
                alert_types.append("Systolic Low")
            elif systolic > BP_THRESHOLDS["systolic"]["max"]:
                alert_types.append("Systolic High")
                
            # Check diastolic
            if diastolic < BP_THRESHOLDS["diastolic"]["min"]:
                alert_types.append("Diastolic Low")
            elif diastolic > BP_THRESHOLDS["diastolic"]["max"]:
                alert_types.append("Diastolic High")
            
            # Fallback for edge cases where model predicts abnormal but values are borderline/normal (false positive handling)
            if not alert_types:
                alert_types.append("Uncertain/Borderline")

            result["anomaly_details"] = {
                "type": ", ".join(alert_types),
                "alert_types": alert_types,
                "probability": float(probabilities[1]),
                "severity": "high" if probabilities[1] > 0.9 else "medium"
            }
        
        return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Train ML model for blood pressure classification"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=10000,
        help="Number of training samples to generate (default: 10000)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Blood Pressure ML Model Training")
    print("=" * 60)
    # Train model
    model = BloodPressureMLModel()
    accuracy = model.train(n_samples=args.samples)
    
    # Save model
    model.save_model()
    
    print("\n" + "=" * 60)
    print("Training Complete")
    print("=" * 60)
    print(f"\nModel saved. Accuracy: {accuracy:.2%}")
    print("\nTo use the model with the consumer:")
    print("  python -m kafka_module.consumer --ml")

