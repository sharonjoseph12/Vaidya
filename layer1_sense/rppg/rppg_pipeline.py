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

    def process_webcam(self, duration: int = 30) -> VitalsResult:
        """Processes webcam feed for rPPG analysis"""
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise FileNotFoundError("Could not open webcam")
            
        raw_signals: Dict[str, List[Tuple[float, float, float]]] = {
            "forehead": [], "left_cheek": [], "right_cheek": []
        }
        
        logger.info(f"Starting webcam recording for {duration} seconds. Please sit still.")
        import time
        start_time = time.time()
        frame_count = 0
        
        while time.time() - start_time < duration:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            # Mirror the frame for better user experience
            frame = cv2.flip(frame, 1)
            
            processed_frame = self.extractor.preprocess_frame(frame)
            landmarks = self.detector.get_landmarks(processed_frame)
            
            if landmarks is not None:
                roi_pixels = self.detector.get_roi_pixels(processed_frame, landmarks)
                means = self.extractor.extract_mean_rgb(roi_pixels)
                
                for name, rgb in means.items():
                    raw_signals[name].append(rgb)
                    
                # Visualize for demo
                display_frame = frame.copy()
                cv2.putText(display_frame, f"Recording: {int(time.time() - start_time)}s / {duration}s", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(display_frame, f"Face detected. Keep still.", 
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            else:
                display_frame = frame.copy()
                cv2.putText(display_frame, "No face detected!", 
                            (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            
            cv2.imshow('PRISM rPPG Demo', display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
        actual_duration = time.time() - start_time
        fps = frame_count / actual_duration if actual_duration > 0 else self.fps
        logger.info(f"Recorded {frame_count} frames over {actual_duration:.2f}s (Average FPS: {fps:.1f})")
        
        if not any(raw_signals.values()):
            raise FaceNotDetectedError("No face detected during recording")
            
        # Update processor and estimator with actual FPS
        self.processor.fps = int(fps)
        self.estimator.fps = int(fps)
        
        # Filter and estimate
        fused_bvp = self.processor.process_modality(raw_signals)
        if len(fused_bvp) < fps * 10: 
            raise InsufficientDataError("Insufficient signal segments extracted for analysis")
            
        vitals = self.estimator.full_vitals(fused_bvp, raw_signals)
        return vitals

if __name__ == "__main__":
    import argparse
    import sys
    import os
    
    # Ensure relative imports work if run directly
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    parser = argparse.ArgumentParser(description="Run PRISM rPPG pipeline")
    parser.add_argument("--source", type=str, default="webcam", help="Video source: 'webcam' or file path")
    parser.add_argument("--duration", type=int, default=30, help="Duration to record from webcam in seconds")
    args = parser.parse_args()
    
    pipeline = PRISMrPPGPipeline(fps=30)
    
    if args.source == "webcam":
        print(f"Starting webcam rPPG. Ensure good lighting and keep your face still.")
        try:
            vitals = pipeline.process_webcam(duration=args.duration)
            print("\n" + "="*40)
            print("rPPG VITALS ESTIMATION RESULTS:")
            print(f"Heart Rate:       {vitals.hr:.1f} BPM")
            print(f"SpO2:             {vitals.spo2:.1f} %")
            print(f"Respiratory Rate: {vitals.rr:.1f} breaths/min")
            print(f"HRV (SDNN):       {vitals.hrv_sdnn:.1f} ms")
            print("="*40 + "\n")
        except Exception as e:
            print(f"\nError processing rPPG: {e}")
    else:
        vitals = pipeline.process_video(args.source)
        print(vitals)
