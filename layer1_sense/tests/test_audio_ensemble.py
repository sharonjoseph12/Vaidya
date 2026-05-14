import pytest
import numpy as np
from layer1_sense.audio.ensemble import PRISMAcousticEnsemble, PRISMSenseResult

def test_ensemble_initialization():
    # Note: This will attempt to download YAMNet on first run
    ensemble = PRISMAcousticEnsemble()
    assert ensemble.diseases == ["TB", "COVID", "Pneumonia", "Asthma", "COPD", "Healthy"]
    assert ensemble.yamnet is not None

def test_ensemble_prediction_format():
    ensemble = PRISMAcousticEnsemble()
    # Create 1 second of white noise
    dummy_audio = np.random.uniform(-1, 1, 22050).astype(np.float32)
    
    result = ensemble.predict(dummy_audio)
    
    assert isinstance(result, PRISMSenseResult)
    assert len(result.disease_probabilities) == 6
    assert "TB" in result.disease_probabilities
    assert sum(result.disease_probabilities.values()) == pytest.approx(1.0)
    
    # Check uncertainty bounds
    assert len(result.uncertainty_bounds) == 6
    for lower, upper in result.uncertainty_bounds.values():
        assert 0.0 <= lower <= 1.0
        assert 0.0 <= upper <= 1.0
        assert upper >= lower

def test_shap_values_presence():
    ensemble = PRISMAcousticEnsemble()
    dummy_audio = np.random.uniform(-1, 1, 22050).astype(np.float32)
    result = ensemble.predict(dummy_audio)
    
    assert result.shap_values is not None
    assert "Spectral Flux" in result.shap_values
