import cv2
import numpy as np
from typing import Optional
from ..datatypes import FaceROIs, ColorBiomarkers
from ..logger import logger

class PRISMColorBiomarker:
    """Color-space analysis for jaundice, anemia, cyanosis, dengue flush, and pallor."""

    def analyze(self, rois: FaceROIs) -> ColorBiomarkers:
        jaundice = self._jaundice_score(rois.sclera)
        pallor = self._pallor_score(rois.conjunctiva)
        cyanosis = self._cyanosis_score(rois.lips)
        dengue = self._dengue_flush_score(rois.forehead)

        severity = self._jaundice_severity(jaundice)

        return ColorBiomarkers(
            jaundice_score=jaundice,
            jaundice_severity=severity,
            pallor_score=pallor,
            cyanosis_score=cyanosis,
            dengue_flush_score=dengue,
        )

    # ---- Jaundice: Yellow saturation in sclera (HSV) ----
    def _jaundice_score(self, sclera_pixels: np.ndarray) -> float:
        if len(sclera_pixels) == 0:
            return 0.0
        # sclera_pixels is (N, 3) BGR
        hsv = cv2.cvtColor(sclera_pixels.reshape(-1, 1, 3), cv2.COLOR_BGR2HSV).reshape(-1, 3)
        # Yellow hue range ~20-35, high saturation
        yellow_mask = (hsv[:, 0] >= 15) & (hsv[:, 0] <= 40) & (hsv[:, 1] > 40)
        score = float(np.sum(yellow_mask) / len(hsv))
        return np.clip(score, 0.0, 1.0)

    def _jaundice_severity(self, score: float) -> str:
        if score < 0.1:
            return "none"
        elif score < 0.3:
            return "mild"
        elif score < 0.6:
            return "moderate"
        return "severe"

    # ---- Pallor / Anemia: Conjunctival redness ratio ----
    def _pallor_score(self, conj_pixels: np.ndarray) -> float:
        if len(conj_pixels) == 0:
            return 0.0
        # BGR order
        r = conj_pixels[:, 2].astype(float)
        g = conj_pixels[:, 1].astype(float)
        b = conj_pixels[:, 0].astype(float)
        # Redness ratio: R / (R+G+B)
        total = r + g + b + 1e-6
        redness = np.mean(r / total)
        # Low redness → high pallor (anemia indicator)
        # Healthy conjunctiva typically has redness > 0.4
        pallor = float(np.clip(1.0 - (redness / 0.45), 0.0, 1.0))
        return pallor

    # ---- Cyanosis: Blue dominance in lips ----
    def _cyanosis_score(self, lip_pixels: np.ndarray) -> float:
        if len(lip_pixels) == 0:
            return 0.0
        b = lip_pixels[:, 0].astype(float)
        g = lip_pixels[:, 1].astype(float)
        r = lip_pixels[:, 2].astype(float)
        total = r + g + b + 1e-6
        blue_ratio = np.mean(b / total)
        # Elevated blue ratio → cyanosis
        score = float(np.clip((blue_ratio - 0.30) / 0.10, 0.0, 1.0))
        return score

    # ---- Dengue Flush: Periorbital redness ----
    def _dengue_flush_score(self, forehead_pixels: np.ndarray) -> float:
        if len(forehead_pixels) == 0:
            return 0.0
        r = forehead_pixels[:, 2].astype(float)
        g = forehead_pixels[:, 1].astype(float)
        # Flush = elevated R relative to G
        ratio = np.mean(r / (g + 1e-6))
        score = float(np.clip((ratio - 1.1) / 0.3, 0.0, 1.0))
        return score
