import numpy as np
import librosa
from typing import List, Tuple
from ..datatypes import CoughSegment

class PRISMCoughDetector:
    def __init__(self, sample_rate: int = 16000, energy_threshold: float = 0.05, min_cough_duration: float = 0.2):
        self.sr = sample_rate
        self.energy_threshold = energy_threshold
        self.min_duration = min_cough_duration

    def detect_coughs(self, audio: np.ndarray) -> List[CoughSegment]:
        """Detects candidate cough segments using energy thresholding"""
        # Calculate Short-Term Energy
        hop_length = 512
        ste = librosa.feature.rms(y=audio, hop_length=hop_length)[0]
        ste = (ste - np.min(ste)) / (np.max(ste) - np.min(ste) + 1e-6)
        
        # Thresholding
        is_cough = ste > self.energy_threshold
        
        segments = []
        start_idx = None
        
        for i, active in enumerate(is_cough):
            if active and start_idx is None:
                start_idx = i
            elif not active and start_idx is not None:
                duration = (i - start_idx) * hop_length / self.sr
                if duration >= self.min_duration:
                    segments.append(CoughSegment(
                        start_time=start_idx * hop_length / self.sr,
                        end_time=i * hop_length / self.sr,
                        confidence=float(ste[start_idx:i].mean())
                    ))
                start_idx = None
                
        return segments

    def extract_segments(self, audio: np.ndarray, segments: List[CoughSegment]) -> List[np.ndarray]:
        """Crops audio into segments"""
        cropped = []
        for seg in segments:
            start = int(seg.start_time * self.sr)
            end = int(seg.end_time * self.sr)
            cropped.append(audio[start:end])
        return cropped
