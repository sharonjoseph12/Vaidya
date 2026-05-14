import numpy as np
import parselmouth
from typing import Dict
from ..datatypes import VoiceBiomarkers

class PRISMVoiceBiomarkerExtractor:
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate

    def extract_voice_metrics(self, audio: np.ndarray) -> VoiceBiomarkers:
        """Extracts jitter, shimmer, HNR using Praat (Parselmouth)"""
        try:
            # Convert to Parselmouth Sound
            sound = parselmouth.Sound(audio, sampling_frequency=self.sr)
            
            # Pitch extraction
            pitch = sound.to_pitch()
            pulses = parselmouth.praat.call([sound, pitch], "To PointProcess (cc)")
            
            # jitter (local)
            jitter = parselmouth.praat.call(pulses, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
            
            # shimmer (local)
            shimmer = parselmouth.praat.call([sound, pulses], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
            
            # HNR
            harmonicity = sound.to_harmonicity()
            hnr = parselmouth.praat.call(harmonicity, "Get mean", 0, 0)
            
            return VoiceBiomarkers(
                jitter=float(jitter),
                shimmer=float(shimmer),
                hnr=float(hnr)
            )
        except Exception:
            return VoiceBiomarkers(jitter=0.0, shimmer=0.0, hnr=0.0)
