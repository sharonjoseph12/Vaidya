import os
import numpy as np
import librosa
import joblib
from typing import Dict, List, Optional
from ..logger import logger

class PRISMCoughClassifier:
    def __init__(self, model_path: Optional[str] = None):
        # Default path to the trained XGBoost model
        if model_path is None:
            model_path = os.path.join(os.path.dirname(__file__), "models", "cough_xgboost_model.pkl")
        
        self.model_path = model_path
        self.model = None
        self.classes = ["Healthy", "Sick"] # Binary classification for now
        
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info(f"Loaded PRISM XGBoost Cough Model from {self.model_path}")
            else:
                logger.warning(f"Cough model not found at {self.model_path}. Predict will return default probs.")
        except Exception as e:
            logger.error(f"Failed to load XGBoost model: {e}")

    def _extract_features(self, waveform: np.ndarray, sr: int = 16000) -> Optional[np.ndarray]:
        """Extracts 13 MFCCs and 1 ZCR from a waveform (consistent with training)"""
        try:
            # Ensure waveform is float32
            y = waveform.astype(np.float32)
            
            # Extract features
            mfccs_mean = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T, axis=0)
            zcr_mean = np.mean(librosa.feature.zero_crossing_rate(y).T, axis=0)
            
            return np.hstack([mfccs_mean, zcr_mean])
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            return None

    def predict(self, audio_segments: List[np.ndarray]) -> Dict[str, float]:
        """Classifies an ensemble of cough segments using the XGBoost model"""
        if not audio_segments or self.model is None:
            n = 8
            u = 1.0 / n
            return {
                "TB": u,
                "COVID": u,
                "Pneumonia": u,
                "Whooping": u,
                "Asthma": u,
                "COPD": u,
                "Healthy": u,
                "Uncertain": u,
            }

        segment_features = []
        for segment in audio_segments:
            feat = self._extract_features(segment)
            if feat is not None:
                segment_features.append(feat)

        if not segment_features:
            n = 8
            u = 1.0 / n
            return {
                "TB": u,
                "COVID": u,
                "Pneumonia": u,
                "Whooping": u,
                "Asthma": u,
                "COPD": u,
                "Healthy": u,
                "Uncertain": u,
            }

        # Run prediction
        X = np.array(segment_features)
        # XGBoost predict_proba returns [P(Healthy), P(Sick)]
        probs_matrix = self.model.predict_proba(X)

        # Ensemble averaging over segments
        avg_probs = np.mean(probs_matrix, axis=0)

        healthy = float(avg_probs[0])
        sick = float(avg_probs[1])
        # Binary model does not separate TB vs COVID: map sick mass to Uncertain, not fake disease splits.
        return {
            "TB": 0.0,
            "COVID": 0.0,
            "Pneumonia": 0.0,
            "Whooping": 0.0,
            "Asthma": 0.0,
            "COPD": 0.0,
            "Healthy": healthy,
            "Uncertain": sick,
        }

