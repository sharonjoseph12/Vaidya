import numpy as np
from scipy import signal
from typing import Tuple, Dict, List
from ..datatypes import VitalsResult

class PRISMVitalsEstimator:
    def __init__(self, fps: int = 30):
        self.fps = fps

    def estimate_hr(self, bvp_signal: np.ndarray) -> float:
        """Estimates HR using Welch Periodogram"""
        freqs, psd = signal.welch(bvp_signal, fs=self.fps, nperseg=len(bvp_signal))
        
        # Focus on [0.7, 4.0] Hz (42-240 BPM)
        valid_indices = np.where((freqs >= 0.7) & (freqs <= 4.0))[0]
        if len(valid_indices) == 0:
            return 0.0
            
        peak_idx = valid_indices[np.argmax(psd[valid_indices])]
        hr = freqs[peak_idx] * 60
        return float(hr)

    def estimate_hrv(self, bvp_signal: np.ndarray) -> Tuple[float, float, float]:
        """Estimates RMSSD, SDNN, and LF/HF ratio"""
        # Peak detection for IBI (Inter-Beat Intervals)
        peaks, _ = signal.find_peaks(bvp_signal, distance=int(self.fps * 0.5))
        if len(peaks) < 2:
            return 0.0, 0.0, 0.0
            
        ibis = np.diff(peaks) / self.fps * 1000 # in ms
        
        # RMSSD
        diff_ibis = np.diff(ibis)
        rmssd = np.sqrt(np.mean(diff_ibis**2))
        
        # SDNN
        sdnn = np.std(ibis)
        
        # LF/HF (Simple frequency bands estimation)
        # Low Frequency (LF): 0.04–0.15 Hz
        # High Frequency (HF): 0.15–0.40 Hz
        # Note: Short-term recording (30s) is barely enough for LF, but providing placeholder
        lf_hf = 1.0 # Placeholder
        
        return float(rmssd), float(sdnn), float(lf_hf)

    def estimate_spo2(self, red_signal: np.ndarray, blue_signal: np.ndarray) -> float:
        """
        Estimates SpO2 using the ratio-of-ratios method.
        Note: This is a placeholder for clinical calibration.
        """
        def get_ac_dc(s):
            dc = np.mean(s)
            ac = np.std(s)
            return ac, dc
            
        ac_red, dc_red = get_ac_dc(red_signal)
        ac_blue, dc_blue = get_ac_dc(blue_signal)
        
        if dc_red == 0 or dc_blue == 0 or ac_blue == 0:
            return 98.0
            
        r = (ac_red / dc_red) / (ac_blue / dc_blue)
        
        # SpO2 = A - B*R (Placeholder calibration A=110, B=25)
        spo2 = 110 - 25 * r
        return float(np.clip(spo2, 85, 100))

    def estimate_rr(self, bvp_signal: np.ndarray) -> float:
        """Estimates Respiratory Rate from BVP amplitude modulation"""
        # Lower frequency band for breathing (0.1 to 0.5 Hz)
        # Extract envelope
        analytic_signal = signal.hilbert(bvp_signal)
        amplitude_envelope = np.abs(analytic_signal)
        
        # Find peaks in envelope
        freqs, psd = signal.welch(amplitude_envelope, fs=self.fps, nperseg=len(amplitude_envelope))
        valid_indices = np.where((freqs >= 0.1) & (freqs <= 0.6))[0]
        
        if len(valid_indices) == 0:
            return 16.0
            
        peak_idx = valid_indices[np.argmax(psd[valid_indices])]
        rr = freqs[peak_idx] * 60
        return float(rr)

    def full_vitals(self, bvp_signal: np.ndarray, rgb_raw: Dict[str, List[Tuple[float, float, float]]]) -> VitalsResult:
        hr = self.estimate_hr(bvp_signal)
        rmssd, sdnn, lfhf = self.estimate_hrv(bvp_signal)
        rr = self.estimate_rr(bvp_signal)
        
        # For SpO2, we need Red and Blue channels from forehead or cheeks
        forehead_raw = np.array(rgb_raw.get("forehead", []))
        if len(forehead_raw) > 0:
            spo2 = self.estimate_spo2(forehead_raw[:, 0], forehead_raw[:, 2])
        else:
            spo2 = 98.0
            
        return VitalsResult(
            hr=hr,
            spo2=spo2,
            hrv_rmssd=rmssd,
            hrv_sdnn=sdnn,
            lf_hf_ratio=lfhf,
            rr=rr,
            confidence_scores={"hr_snr": 0.8} # Placeholder
        )
