import numpy as np
from scipy import signal
from typing import List, Dict, Tuple

class PRISMrPPGProcessor:
    """CHROM-based rPPG signal processor.

    Implements the Chrominance (CHROM) method for extracting blood-volume-pulse
    signals from RGB facial video. Includes bandpass filtering (0.7–4.0 Hz)
    and multi-ROI signal fusion.

    Reference: de Haan & Jeanne, "Robust Pulse Rate From Chrominance-Based rPPG", 2013.
    """

    def __init__(self, fps: int = 30, lowcut: float = 0.7, highcut: float = 4.0):
        self.fps = fps
        self.lowcut = lowcut
        self.highcut = highcut

    def bandpass_filter(self, data: np.ndarray) -> np.ndarray:
        nyq = 0.5 * self.fps
        low = self.lowcut / nyq
        high = self.highcut / nyq
        b, a = signal.butter(4, [low, high], btype='band')
        return signal.filtfilt(b, a, data)

    def chrom_method(self, rgb_signals: np.ndarray) -> np.ndarray:
        """
        Implements CHROM method for rPPG.
        rgb_signals: (T, 3) array where 3 is (R, G, B)
        """
        # Normalize signals
        mean_rgb = np.mean(rgb_signals, axis=0)
        norm_rgb = rgb_signals / mean_rgb
        
        # Xs = 3*Rn - 2*Gn
        # Ys = 1.5*Rn + Gn - 1.5*Bn
        xs = 3 * norm_rgb[:, 0] - 2 * norm_rgb[:, 1]
        ys = 1.5 * norm_rgb[:, 0] + norm_rgb[:, 1] - 1.5 * norm_rgb[:, 2]
        
        # Standardize
        xs_std = np.std(xs)
        ys_std = np.std(ys)
        
        # alpha = std(xs)/std(ys)
        alpha = xs_std / ys_std if ys_std != 0 else 0
        
        # S = Xs - alpha*Ys
        s = xs - alpha * ys
        
        return s

    def process_modality(self, raw_signals: Dict[str, List[Tuple[float, float, float]]]) -> np.ndarray:
        """
        Fuses multiple ROIs into a single filtered rPPG signal.
        raw_signals: {roi_name: [(R,G,B), ...]}
        """
        processed_signals = []
        
        for name, data in raw_signals.items():
            if not data: continue
            rgb_array = np.array(data)
            
            # 1. Apply CHROM
            bvp = self.chrom_method(rgb_array)
            
            # 2. Detrend
            bvp = signal.detrend(bvp)
            
            # 3. Bandpass filter
            bvp = self.bandpass_filter(bvp)
            
            processed_signals.append(bvp)
            
        if not processed_signals:
            return np.array([])
            
        # Fusion: Simple averaging for now, SNR-weighting would be US1 polish
        fused_signal = np.mean(processed_signals, axis=0)
        return fused_signal
