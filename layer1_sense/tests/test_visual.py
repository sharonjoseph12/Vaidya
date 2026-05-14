import pytest
import numpy as np
from ..visual.color_biomarker import PRISMColorBiomarker
from ..visual.disease_classifier import PRISMVisualClassifier
from ..datatypes import FaceROIs

def _make_solid_roi(b, g, r, n=500):
    """Helper: create N pixels of a solid BGR color."""
    return np.full((n, 3), [b, g, r], dtype=np.uint8)

def test_color_biomarker_baseline():
    """Neutral skin tones should produce low scores across all biomarkers."""
    bio = PRISMColorBiomarker()
    rois = FaceROIs(
        forehead=_make_solid_roi(160, 170, 180),
        left_cheek=_make_solid_roi(160, 170, 180),
        right_cheek=_make_solid_roi(160, 170, 180),
        sclera=_make_solid_roi(240, 240, 240),       # white sclera
        conjunctiva=_make_solid_roi(100, 120, 200),   # reddish conjunctiva
        lips=_make_solid_roi(100, 100, 170),          # pinkish lips
    )
    result = bio.analyze(rois)
    assert result.jaundice_score < 0.3, f"Expected low jaundice, got {result.jaundice_score}"
    assert result.jaundice_severity in ("none", "mild")

def test_color_biomarker_jaundice():
    """Yellow sclera should trigger high jaundice score."""
    bio = PRISMColorBiomarker()
    # Yellow in BGR: B~0, G~200, R~255
    rois = FaceROIs(
        forehead=_make_solid_roi(160, 170, 180),
        left_cheek=_make_solid_roi(160, 170, 180),
        right_cheek=_make_solid_roi(160, 170, 180),
        sclera=_make_solid_roi(30, 210, 240),  # bright yellow sclera
        conjunctiva=_make_solid_roi(100, 120, 200),
        lips=_make_solid_roi(100, 100, 170),
    )
    result = bio.analyze(rois)
    assert result.jaundice_score > 0.3, f"Expected high jaundice, got {result.jaundice_score}"

def test_classifier_output_shape():
    """Classifier should return scores for all expected tasks."""
    clf = PRISMVisualClassifier(pretrained=False)
    fake_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    scores = clf.predict(fake_frame)

    expected_keys = {"anemia", "cyanosis", "dengue", "jaundice_none", "jaundice_mild", "jaundice_moderate", "jaundice_severe"}
    assert expected_keys == set(scores.keys()), f"Unexpected keys: {set(scores.keys())}"

    for v in scores.values():
        assert 0.0 <= v <= 1.0, f"Score out of range: {v}"
