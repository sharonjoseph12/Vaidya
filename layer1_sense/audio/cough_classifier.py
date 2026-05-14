import numpy as np
import tensorflow as tf
import tensorflow_hub as hub
from typing import Dict, List, Optional
from ..logger import logger

class PRISMCoughClassifier:
    def __init__(self, model_path: Optional[str] = None):
        # Load YAMNet from TF Hub
        try:
            self.yamnet = hub.load('https://tfhub.dev/google/yamnet/1')
            logger.info("Loaded YAMNet from TF Hub")
        except Exception as e:
            logger.error(f"Failed to load YAMNet: {e}")
            self.yamnet = None
            
        self.classes = ["TB", "COVID", "Pneumonia", "Whooping", "Asthma", "COPD", "Healthy", "Uncertain"]
        # Placeholder for custom classification head weights
        self.custom_head = None 

    def predict(self, audio_segments: List[np.ndarray]) -> Dict[str, float]:
        """Classifies an ensemble of cough segments"""
        if not audio_segments or self.yamnet is None:
            return {cls: 1.0/len(self.classes) for cls in self.classes}
            
        segment_probs = []
        
        for segment in audio_segments:
            # YAMNet expects 16kHz mono audio in [-1, 1]
            waveform = segment.astype(np.float32)
            
            # Run YAMNet
            scores, embeddings, spectrogram = self.yamnet(waveform)
            
            # Average scores over time for the segment
            mean_scores = tf.reduce_mean(scores, axis=0).numpy()
            
            # Map YAMNet respiratory classes to PRISM diseases
            # 36: Breathing, 37: Wheeze, 42: Cough, 43: Throat clearing, 45: Sniff
            breathing = float(mean_scores[36])
            wheeze = float(mean_scores[37])
            cough = float(mean_scores[42])
            throat = float(mean_scores[43])
            sniff = float(mean_scores[45])
            
            # Simple heuristic map for demo/offline logic
            p_tb = cough * 0.8 + throat * 0.2
            p_covid = cough * 0.6 + sniff * 0.4
            p_pneumonia = cough * 0.7 + breathing * 0.3
            p_whooping = cough * 0.9 + wheeze * 0.1
            p_asthma = wheeze * 0.8 + cough * 0.2
            p_copd = wheeze * 0.6 + breathing * 0.4
            p_healthy = 1.0 - np.clip(cough + wheeze + breathing, 0.0, 1.0)
            
            raw_probs = np.array([p_tb, p_covid, p_pneumonia, p_whooping, p_asthma, p_copd, p_healthy, 0.1])
            probs = raw_probs / (np.sum(raw_probs) + 1e-6)
            segment_probs.append(probs)
            
        # Ensemble averaging
        final_probs = np.mean(segment_probs, axis=0)
        return {cls: float(prob) for cls, prob in zip(self.classes, final_probs)}
