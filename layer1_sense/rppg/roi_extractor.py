import numpy as np
import cv2
from typing import Dict, Tuple

class PRISMROIExtractor:
    def __init__(self, apply_clahe: bool = True):
        self.apply_clahe = apply_clahe
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Applies CLAHE and basic white balancing"""
        if not self.apply_clahe:
            return frame
            
        # Lab color space for CLAHE on L channel
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        cl = self.clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        final_frame = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        # Gray World white balance (simple version)
        # avg_b = np.mean(final_frame[:, :, 0])
        # avg_g = np.mean(final_frame[:, :, 1])
        # avg_r = np.mean(final_frame[:, :, 2])
        # avg = (avg_b + avg_g + avg_r) / 3
        # final_frame[:, :, 0] = np.clip(final_frame[:, :, 0] * (avg / avg_b), 0, 255)
        # final_frame[:, :, 1] = np.clip(final_frame[:, :, 1] * (avg / avg_g), 0, 255)
        # final_frame[:, :, 2] = np.clip(final_frame[:, :, 2] * (avg / avg_r), 0, 255)
        
        return final_frame.astype(np.uint8)

    def extract_mean_rgb(self, roi_pixels: Dict[str, np.ndarray]) -> Dict[str, Tuple[float, float, float]]:
        """Calculates mean R, G, B for each ROI. Note: OpenCV uses BGR order."""
        means = {}
        for name, pixels in roi_pixels.items():
            if len(pixels) == 0:
                means[name] = (0.0, 0.0, 0.0)
                continue
            
            # pixels is (N, 3) in BGR
            mean_bgr = np.mean(pixels, axis=0)
            means[name] = (float(mean_bgr[2]), float(mean_bgr[1]), float(mean_bgr[0])) # Convert to RGB
            
        return means
