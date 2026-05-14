import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from .face_detector import PRISMFaceDetector
from .roi_extractor import PRISMROIExtractor
from .signal_processor import PRISMrPPGProcessor
from .vitals_estimator import PRISMVitalsEstimator
from ..datatypes import VitalsResult
from ..logger import logger
from ..exceptions import FaceNotDetectedError, InsufficientDataError

class PRISMrPPGPipeline:
    def __init__(self, fps: int = 30):
        self.detector = PRISMFaceDetector()
        self.extractor = PRISMROIExtractor()
        self.processor = PRISMrPPGProcessor(fps=fps)
        self.estimator = PRISMVitalsEstimator(fps=fps)
        self.fps = fps

    def process_video(self, video_path: str) -> VitalsResult:
        """Processes a video file for rPPG analysis"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise FileNotFoundError(f"Could not open video at {video_path}")
            
        raw_signals: Dict[str, List[Tuple[float, float, float]]] = {
            "forehead": [], "left_cheek": [], "right_cheek": []
        }
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            processed_frame = self.extractor.preprocess_frame(frame)
            landmarks = self.detector.get_landmarks(processed_frame)
            
            if landmarks is None:
                # Log warning but continue; if too many frames fail, error will be raised later
                continue
                
            roi_pixels = self.detector.get_roi_pixels(processed_frame, landmarks)
            means = self.extractor.extract_mean_rgb(roi_pixels)
            
            for name, rgb in means.items():
                if name in raw_signals:
                    raw_signals[name].append(rgb)
                    
        cap.release()
        
        # Check for minimum duration (30s)
        if frame_count < self.fps * 30:
            logger.warning(f"Video duration ({frame_count/self.fps:.2f}s) is less than 30s recommended")
            
        if not any(raw_signals.values()):
            raise FaceNotDetectedError("No face detected in any frame of the video")
            
        # Filter and estimate
        fused_bvp = self.processor.process_modality(raw_signals)
        if len(fused_bvp) < self.fps * 10: # Minimum 10s for any useful estimate
            raise InsufficientDataError("Insufficient signal segments extracted for analysis")
            
        vitals = self.estimator.full_vitals(fused_bvp, raw_signals)
        return vitals

    def process_frame_stream(self, frame_iterator):
        """Placeholder for real-time stream processing if needed"""
        pass
