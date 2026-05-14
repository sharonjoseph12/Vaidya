import pytest
import numpy as np
from ..rppg.signal_processor import PRISMrPPGProcessor
from ..rppg.vitals_estimator import PRISMVitalsEstimator

def test_signal_processor_chrom():
    fps = 30
    duration = 10
    t = np.linspace(0, duration, fps * duration)
    
    # 1.2 Hz signal (72 BPM)
    pure_signal = np.sin(2 * np.pi * 1.2 * t)
    
    # Create fake RGB signals (R, G, B)
    # Blood absorption is highest in Green, so pulse is strongest there
    r = 100 + 0.1 * pure_signal
    g = 100 + 0.2 * pure_signal
    b = 100 + 0.05 * pure_signal
    
    rgb_signals = np.column_stack((r, g, b))
    
    processor = PRISMrPPGProcessor(fps=fps)
    bvp = processor.chrom_method(rgb_signals)
    
    assert len(bvp) == len(t)
    # CHROM should extract a pulse-like signal
    assert np.std(bvp) > 0

def test_vitals_estimator_hr():
    fps = 30
    duration = 20
    t = np.linspace(0, duration, fps * duration)
    
    # 1.33 Hz signal (80 BPM)
    target_hr = 80.0
    freq = target_hr / 60
    bvp = np.sin(2 * np.pi * freq * t)
    
    estimator = PRISMVitalsEstimator(fps=fps)
    estimated_hr = estimator.estimate_hr(bvp)
    
    # Expect within 2 BPM
    assert abs(estimated_hr - target_hr) < 2.0

def test_vitals_estimator_rr():
    fps = 30
    duration = 60 # RR needs longer segments
    t = np.linspace(0, duration, fps * duration)
    
    # 80 BPM HR modulated by 15 breaths/min (0.25 Hz)
    target_rr = 15.0
    hr_freq = 80 / 60
    rr_freq = target_rr / 60
    
    # Amplitude modulation
    carrier = np.sin(2 * np.pi * hr_freq * t)
    modulator = 1 + 0.5 * np.sin(2 * np.pi * rr_freq * t)
    bvp = carrier * modulator
    
    estimator = PRISMVitalsEstimator(fps=fps)
    estimated_rr = estimator.estimate_rr(bvp)
    
    assert abs(estimated_rr - target_rr) < 2.0
