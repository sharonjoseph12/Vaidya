import cv2
import numpy as np
from typing import Dict, List, Optional
from .face_analyzer import PRISMFaceAnalyzer
from .color_biomarker import PRISMColorBiomarker
from .disease_classifier import PRISMVisualClassifier
from ..datatypes import VisualBiomarkerResult, ColorBiomarkers
from ..logger import logger

class PRISMVisualPipeline:
    """Orchestrates face ROI extraction → color biomarkers + CNN classifier → fused visual output."""

    def __init__(self):
        self.face_analyzer = PRISMFaceAnalyzer()
        self.color_biomarker = PRISMColorBiomarker()
        self.classifier = PRISMVisualClassifier(pretrained=True)

    def analyze_frame(self, frame: np.ndarray) -> Optional[VisualBiomarkerResult]:
        """Analyze a single BGR frame."""
        rois = self.face_analyzer.analyze_frame(frame)
        if rois is None:
            return None

        # Color-based biomarkers
        color_scores = self.color_biomarker.analyze(rois)

        # CNN classifier
        classifier_scores = self.classifier.predict(frame)

        # Cross-validation: flag disagreements
        flags = self._cross_validate(color_scores, classifier_scores)

        return VisualBiomarkerResult(
            color_biomarkers=color_scores,
            classifier_scores=classifier_scores,
            uncertainty_flags=flags,
        )

    def analyze_video(self, video_path: str, sample_every_n: int = 5) -> VisualBiomarkerResult:
        """Analyze a video by sampling frames and computing median aggregation."""
        cap = cv2.VideoCapture(video_path)
        results: List[VisualBiomarkerResult] = []
        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % sample_every_n == 0:
                result = self.analyze_frame(frame)
                if result is not None:
                    results.append(result)
            frame_idx += 1
        cap.release()

        if not results:
            return VisualBiomarkerResult(
                color_biomarkers=ColorBiomarkers(0.0, "none", 0.0, 0.0, 0.0),
                classifier_scores={},
                uncertainty_flags=["no_face_detected"],
            )

        # Median aggregation across frames
        return self._aggregate(results)

    def _aggregate(self, results: List[VisualBiomarkerResult]) -> VisualBiomarkerResult:
        jaundice_scores = [r.color_biomarkers.jaundice_score for r in results]
        pallor_scores = [r.color_biomarkers.pallor_score for r in results]
        cyanosis_scores = [r.color_biomarkers.cyanosis_score for r in results]
        dengue_scores = [r.color_biomarkers.dengue_flush_score for r in results]

        med_j = float(np.median(jaundice_scores))
        med_p = float(np.median(pallor_scores))
        med_c = float(np.median(cyanosis_scores))
        med_d = float(np.median(dengue_scores))

        # Aggregate classifier scores by median
        all_keys = results[0].classifier_scores.keys()
        agg_classifier = {}
        for key in all_keys:
            vals = [r.classifier_scores.get(key, 0.0) for r in results]
            agg_classifier[key] = float(np.median(vals))

        # Collect all flags
        all_flags = set()
        for r in results:
            all_flags.update(r.uncertainty_flags)

        color_bio = PRISMColorBiomarker()
        return VisualBiomarkerResult(
            color_biomarkers=ColorBiomarkers(
                jaundice_score=med_j,
                jaundice_severity=color_bio._jaundice_severity(med_j),
                pallor_score=med_p,
                cyanosis_score=med_c,
                dengue_flush_score=med_d,
            ),
            classifier_scores=agg_classifier,
            uncertainty_flags=list(all_flags),
        )

    def _cross_validate(self, color: ColorBiomarkers, classifier: Dict[str, float]) -> List[str]:
        flags = []
        # Jaundice: color says severe but classifier disagrees
        if color.jaundice_score > 0.5 and classifier.get("jaundice_severe", 0) < 0.2:
            flags.append("jaundice_color_classifier_disagree")
        # Anemia: pallor high but classifier low
        if color.pallor_score > 0.5 and classifier.get("anemia", 0) < 0.3:
            flags.append("anemia_color_classifier_disagree")
        # Cyanosis
        if color.cyanosis_score > 0.5 and classifier.get("cyanosis", 0) < 0.3:
            flags.append("cyanosis_color_classifier_disagree")
        return flags
