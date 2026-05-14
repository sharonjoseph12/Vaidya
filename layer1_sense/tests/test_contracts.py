import pytest
import json
from ..datatypes import (
    SenseResult, VitalsResult, AudioAnalysisResult,
    VisualBiomarkerResult, ColorBiomarkers, VoiceBiomarkers,
)

def _make_sense_result() -> SenseResult:
    return SenseResult(
        disease_probabilities={"TB": 0.1, "COVID": 0.05, "Pneumonia": 0.2,
                               "Whooping_Cough": 0.0, "Asthma": 0.1, "COPD": 0.05,
                               "Jaundice": 0.15, "Anemia": 0.08, "Cyanosis": 0.02,
                               "Dengue": 0.1, "Parkinsons": 0.01, "Healthy": 0.14},
        rppg=VitalsResult(hr=72, spo2=97.5, hrv_rmssd=35, hrv_sdnn=50,
                          lf_hf_ratio=1.2, rr=16, confidence_scores={"hr_snr": 0.85}),
        audio=AudioAnalysisResult(
            cough_detected=True, breathing_rate=15.0,
            abnormal_sounds={"wheeze": "none"},
            voice_biomarkers=VoiceBiomarkers(0.01, 0.03, 15.0),
            disease_probs={"TB": 0.1, "Healthy": 0.4},
        ),
        visual=VisualBiomarkerResult(
            color_biomarkers=ColorBiomarkers(0.2, "mild", 0.1, 0.05, 0.15),
            classifier_scores={"anemia": 0.15, "cyanosis": 0.05},
        ),
        uncertainty={"TB": (0.1, 0.02), "COVID": (0.05, 0.01), "Pneumonia": (0.2, 0.03),
                     "Whooping_Cough": (0.0, 0.0), "Asthma": (0.1, 0.02), "COPD": (0.05, 0.01),
                     "Jaundice": (0.15, 0.02), "Anemia": (0.08, 0.01), "Cyanosis": (0.02, 0.005),
                     "Dengue": (0.1, 0.02), "Parkinsons": (0.01, 0.005), "Healthy": (0.14, 0.02)},
        processing_time_ms=342,
    )

def test_contract_keys():
    """SenseResult.to_dict() must contain the exact contract keys."""
    result = _make_sense_result()
    d = result.to_dict()

    required_keys = {"disease_probabilities", "rppg", "audio", "visual", "uncertainty", "processing_time_ms"}
    assert set(d.keys()) == required_keys

def test_json_roundtrip():
    """Serialize to JSON and deserialize back — all data must survive."""
    original = _make_sense_result()
    json_str = original.to_json()

    # Must be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)

    # Roundtrip
    restored = SenseResult.from_json(json_str)
    assert restored.disease_probabilities == original.disease_probabilities
    assert restored.rppg.hr == original.rppg.hr
    assert restored.audio.cough_detected == original.audio.cough_detected
    assert restored.visual.color_biomarkers.jaundice_score == original.visual.color_biomarkers.jaundice_score
    assert restored.processing_time_ms == original.processing_time_ms

def test_uncertainty_structure():
    """Uncertainty dict must have (mean, std) tuples for every disease."""
    result = _make_sense_result()
    d = result.to_dict()

    for disease, bounds in d["uncertainty"].items():
        assert len(bounds) == 2, f"Expected 2-element list for {disease}"
        assert isinstance(bounds[0], float)
        assert isinstance(bounds[1], float)
        assert bounds[1] >= 0, f"Std must be non-negative for {disease}"
