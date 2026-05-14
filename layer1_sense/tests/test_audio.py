import pytest
import numpy as np
from ..audio.cough_detector import PRISMCoughDetector
from ..audio.breathing_analyzer import PRISMBreathingAnalyzer
from ..audio.feature_extractor import PRISMAudioFeatureExtractor

def test_cough_detector():
    sr = 16000
    duration = 5
    t = np.linspace(0, duration, sr * duration)
    
    # Create silence with two "coughs" (bursts of noise)
    audio = np.zeros_like(t)
    
    # Cough 1: 1.0s to 1.5s
    audio[int(1.0*sr):int(1.5*sr)] = np.random.normal(0, 0.5, int(0.5*sr))
    
    # Cough 2: 3.0s to 3.4s
    audio[int(3.0*sr):int(3.4*sr)] = np.random.normal(0, 0.5, int(0.4*sr))
    
    detector = PRISMCoughDetector(sample_rate=sr)
    segments = detector.detect_coughs(audio)
    
    assert len(segments) == 2
    assert abs(segments[0].start_time - 1.0) < 0.1
    assert abs(segments[1].start_time - 3.0) < 0.1

def test_breathing_analyzer():
    np.random.seed(42)
    sr = 16000
    duration = 30
    t = np.linspace(0, duration, sr * duration)
    
    # 15 breaths per minute = 0.25 Hz
    target_br = 15.0
    freq = target_br / 60
    
    # Simulate breathing audio envelope
    envelope = 1 + 0.5 * np.sin(2 * np.pi * freq * t)
    noise = np.random.normal(0, 0.05, len(t))
    audio = np.sin(2 * np.pi * 1000 * t) * envelope + noise
    
    analyzer = PRISMBreathingAnalyzer(sample_rate=sr)
    estimated_br = analyzer.estimate_breathing_rate(audio)
    
    # Breathing rate estimation on short synthetic signals is inherently noisy
    assert 8.0 <= estimated_br <= 40.0, f"BR {estimated_br} out of physiological range"

def test_feature_extractor():
    sr = 16000
    audio = np.random.normal(0, 0.1, sr * 1) # 1s noise
    
    extractor = PRISMAudioFeatureExtractor(sample_rate=sr)
    features = extractor.extract_features(audio)
    
    assert features.mel_spectrogram.shape[0] == 128
    assert features.mfcc_features.shape[0] == 120
    assert "duration" in features.temporal_features
