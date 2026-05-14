import librosa
import numpy as np
from typing import Dict, List, Optional
from .cough_detector import PRISMCoughDetector
from .feature_extractor import PRISMAudioFeatureExtractor
from .cough_classifier import PRISMCoughClassifier
from .breathing_analyzer import PRISMBreathingAnalyzer
from .voice_biomarker import PRISMVoiceBiomarkerExtractor
from ..datatypes import AudioAnalysisResult, VoiceBiomarkers
from ..logger import logger

class PRISMAudioPipeline:
    def __init__(self, sample_rate: int = 16000):
        self.sr = sample_rate
        self.detector = PRISMCoughDetector(sample_rate=sample_rate)
        self.extractor = PRISMAudioFeatureExtractor(sample_rate=sample_rate)
        self.classifier = PRISMCoughClassifier()
        self.breathing = PRISMBreathingAnalyzer(sample_rate=sample_rate)
        self.voice = PRISMVoiceBiomarkerExtractor(sample_rate=sample_rate)

    def full_analysis(self, audio_path: str) -> AudioAnalysisResult:
        """Runs the full audio biomarker analysis pipeline"""
        try:
            audio, _ = librosa.load(audio_path, sr=self.sr)
        except Exception as e:
            logger.error(f"Failed to load audio file: {e}")
            return self._empty_result()
            
        # 1. Cough Detection and Classification
        cough_segments = self.detector.detect_coughs(audio)
        cough_audio = self.detector.extract_segments(audio, cough_segments)
        disease_probs = self.classifier.predict(cough_audio)
        
        # 2. Breathing Rate
        breathing_rate = self.breathing.estimate_breathing_rate(audio)
        abnormal_sounds = self.breathing.detect_abnormal_sounds(audio)
        
        # 3. Voice Biomarkers
        voice_metrics = self.voice.extract_voice_metrics(audio)
        
        return AudioAnalysisResult(
            cough_detected=len(cough_segments) > 0,
            breathing_rate=breathing_rate,
            abnormal_sounds=abnormal_sounds,
            voice_biomarkers=voice_metrics,
            disease_probs=disease_probs
        )

    def _empty_result(self) -> AudioAnalysisResult:
        return AudioAnalysisResult(
            cough_detected=False,
            breathing_rate=0.0,
            abnormal_sounds={},
            voice_biomarkers=VoiceBiomarkers(0.0, 0.0, 0.0),
            disease_probs={}
        )
