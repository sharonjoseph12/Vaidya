import cv2
import mediapipe as mp
import numpy as np
from typing import Optional, Tuple, Dict, List
from ..exceptions import FaceNotDetectedError
from ..logger import logger

class PRISMFaceDetector:
    """MediaPipe FaceMesh-based face detector for rPPG ROI extraction.

    Detects 478 facial landmarks and segments forehead/cheek ROIs
    for downstream RGB signal extraction.
    """

    def __init__(self, static_image_mode: bool = False, max_num_faces: int = 1):
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=static_image_mode,
            max_num_faces=max_num_faces,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Landmark indices for ROIs from config would be better, but pinning common ones for now
        # Indices are based on MediaPipe FaceMesh canonical model
        self.roi_indices = {
            "forehead": [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109],
            "left_cheek": [117, 118, 119, 100, 126, 209, 198, 131],
            "right_cheek": [346, 347, 348, 329, 355, 429, 420, 360]
        }

    def get_landmarks(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """Detect facial landmarks from a BGR frame.

        Args:
            frame: BGR image as ``(H, W, 3)`` uint8 array.

        Returns:
            ``(N, 3)`` landmark coordinates in pixel space, or ``None``
            if no face is detected.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return None
            
        face_landmarks = results.multi_face_landmarks[0]
        h, w, _ = frame.shape
        landmarks = np.array([[lm.x * w, lm.y * h, lm.z * w] for lm in face_landmarks.landmark])
        return landmarks

    def extract_roi_masks(self, frame: np.ndarray, landmarks: np.ndarray) -> Dict[str, np.ndarray]:
        """Returns binary masks for each ROI"""
        h, w, _ = frame.shape
        masks = {}
        
        for name, indices in self.roi_indices.items():
            mask = np.zeros((h, w), dtype=np.uint8)
            points = landmarks[indices][:, :2].astype(np.int32)
            hull = cv2.convexHull(points)
            cv2.fillConvexPoly(mask, hull, 255)
            masks[name] = mask
            
        return masks

    def get_roi_pixels(self, frame: np.ndarray, landmarks: np.ndarray) -> Dict[str, np.ndarray]:
        """Returns pixels within each ROI as (N, 3) array"""
        masks = self.extract_roi_masks(frame, landmarks)
        roi_pixels = {}
        
        for name, mask in masks.items():
            pixels = frame[mask > 0]
            roi_pixels[name] = pixels
            
        return roi_pixels
