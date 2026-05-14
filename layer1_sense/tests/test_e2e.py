import pytest
import torch
import numpy as np
from ..sense_pipeline import PRISMSensePipeline
from ..fusion.cross_modal_fusion import PRISMFusionModel
from ..datatypes import (
    VitalsResult, AudioAnalysisResult, VisualBiomarkerResult,
    ColorBiomarkers, VoiceBiomarkers,
)

def test_e2e_featurization_and_fusion():
    """Test the full featurize → fuse path with synthetic modality outputs."""
    pipeline = PRISMSensePipeline()

    # Construct fake modality results
    rppg = VitalsResult(hr=72, spo2=97.5, hrv_rmssd=35, hrv_sdnn=50,
                        lf_hf_ratio=1.2, rr=16, confidence_scores={"hr_snr": 0.85})
    audio = AudioAnalysisResult(
        cough_detected=True, breathing_rate=15.0,
        abnormal_sounds={"wheeze": "none"},
        voice_biomarkers=VoiceBiomarkers(0.01, 0.03, 15.0),
        disease_probs={"TB": 0.1, "COVID": 0.05, "Pneumonia": 0.2,
                       "Whooping": 0.0, "Asthma": 0.1, "COPD": 0.05,
                       "Healthy": 0.4, "Uncertain": 0.1},
    )
    visual = VisualBiomarkerResult(
        color_biomarkers=ColorBiomarkers(0.2, "mild", 0.1, 0.05, 0.15),
        classifier_scores={"anemia": 0.15, "cyanosis": 0.05, "dengue": 0.1,
                           "jaundice_none": 0.5, "jaundice_mild": 0.3,
                           "jaundice_moderate": 0.15, "jaundice_severe": 0.05},
    )

    # Featurize
    rppg_t = pipeline._rppg_to_tensor(rppg)
    audio_t = pipeline._audio_to_tensor(audio)
    visual_t = pipeline._visual_to_tensor(visual)

    assert rppg_t.shape == (1, 7)
    assert audio_t.shape == (1, 16)
    assert visual_t.shape == (1, 11)

    # Run fusion
    mean_probs, std_probs = pipeline.fusion.predict_with_uncertainty(
        rppg_t, audio_t, visual_t, n_passes=5,
    )
    assert mean_probs.shape == (1, 12)
    assert (mean_probs >= 0).all() and (mean_probs <= 1).all()
    assert (std_probs >= 0).all()

def test_e2e_output_contract():
    """SenseResult must contain all required keys for Layer 2/3 consumption."""
    pipeline = PRISMSensePipeline()

    # Build a SenseResult manually (no real files)
    rppg = VitalsResult(hr=72, spo2=97.5, hrv_rmssd=35, hrv_sdnn=50,
                        lf_hf_ratio=1.2, rr=16, confidence_scores={})
    audio = AudioAnalysisResult(False, 0, {}, VoiceBiomarkers(0, 0, 0), {})
    visual = VisualBiomarkerResult(ColorBiomarkers(0, "none", 0, 0, 0), {}, [])

    rppg_t = pipeline._rppg_to_tensor(rppg)
    audio_t = pipeline._audio_to_tensor(audio)
    visual_t = pipeline._visual_to_tensor(visual)

    mean_probs, std_probs = pipeline.fusion.predict_with_uncertainty(
        rppg_t, audio_t, visual_t, n_passes=5,
    )

    disease_probs = {
        name: float(mean_probs[0, i])
        for i, name in enumerate(PRISMFusionModel.DISEASES)
    }
    uncertainty = {
        name: (float(mean_probs[0, i]), float(std_probs[0, i]))
        for i, name in enumerate(PRISMFusionModel.DISEASES)
    }

    from ..datatypes import SenseResult
    result = SenseResult(
        disease_probabilities=disease_probs,
        rppg=rppg,
        audio=audio,
        visual=visual,
        uncertainty=uncertainty,
        processing_time_ms=42,
    )

    # Contract: 12 diseases
    assert len(result.disease_probabilities) == 12
    for p in result.disease_probabilities.values():
        assert 0.0 <= p <= 1.0

    # Contract: uncertainty bounds present for every disease
    assert set(result.disease_probabilities.keys()) == set(result.uncertainty.keys())
    for name, (mean, std) in result.uncertainty.items():
        assert std >= 0

    assert result.processing_time_ms >= 0
