import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, Optional
from ..datatypes import FaceROIs
from ..logger import logger

class PRISMFaceAnalyzer:
    """Segments face into clinical ROIs (sclera, conjunctiva, lips, skin) using MediaPipe landmarks."""

    # MediaPipe FaceMesh landmark indices for clinical ROIs
    SCLERA_LEFT = [33, 7, 163, 144, 145, 153, 154, 155, 133]
    SCLERA_RIGHT = [362, 382, 381, 380, 374, 373, 390, 249, 263]
    CONJUNCTIVA_LEFT = [33, 246, 161, 160, 159, 158, 157, 173, 133]
    CONJUNCTIVA_RIGHT = [362, 398, 384, 385, 386, 387, 388, 466, 263]
    LIPS_OUTER = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
    FOREHEAD = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
    LEFT_CHEEK = [117, 118, 119, 100, 126, 209, 198, 131]
    RIGHT_CHEEK = [346, 347, 348, 329, 355, 429, 420, 360]

    def __init__(self):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5
        )

    def _get_roi_mask(self, frame: np.ndarray, landmarks: np.ndarray, indices: list) -> np.ndarray:
        h, w = frame.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        points = landmarks[indices][:, :2].astype(np.int32)
        hull = cv2.convexHull(points)
        cv2.fillConvexPoly(mask, hull, (255,))
        return mask

    def _get_roi_pixels(self, frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
        return frame[mask > 0]

    def analyze_frame(self, frame: np.ndarray) -> Optional[FaceROIs]:
        """Extracts all clinical ROI pixel arrays from a single frame."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb)

        landmarks_list = getattr(results, 'multi_face_landmarks', None)
        if not landmarks_list:
            return None
            
        face = landmarks_list[0]
        h, w = frame.shape[:2]
        landmarks = np.array([[lm.x * w, lm.y * h, lm.z * w] for lm in face.landmark])

        roi_map = {
            "sclera": self.SCLERA_LEFT + self.SCLERA_RIGHT,
            "conjunctiva": self.CONJUNCTIVA_LEFT + self.CONJUNCTIVA_RIGHT,
            "lips": self.LIPS_OUTER,
            "forehead": self.FOREHEAD,
            "left_cheek": self.LEFT_CHEEK,
            "right_cheek": self.RIGHT_CHEEK,
        }

        extracted = {}
        for name, indices in roi_map.items():
            mask = self._get_roi_mask(frame, landmarks, indices)
            extracted[name] = self._get_roi_pixels(frame, mask)

        return FaceROIs(
            forehead=extracted["forehead"],
            left_cheek=extracted["left_cheek"],
            right_cheek=extracted["right_cheek"],
            sclera=extracted["sclera"],
            conjunctiva=extracted["conjunctiva"],
            lips=extracted["lips"],
        )
