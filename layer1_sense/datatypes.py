from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

@dataclass
class VitalsResult:
    hr: float
    spo2: float
    hrv_rmssd: float
    hrv_sdnn: float
    lf_hf_ratio: float
    rr: float
    confidence_scores: Dict[str, float] = field(default_factory=dict)

@dataclass
class CoughSegment:
    start_time: float
    end_time: float
    confidence: float

@dataclass
class AcousticFeatures:
    mel_spectrogram: Any  # np.ndarray
    mfcc_features: Any
    chroma_stft: Any
    spectral_features: Any
    temporal_features: Dict[str, float]

@dataclass
class VoiceBiomarkers:
    jitter: float
    shimmer: float
    hnr: float

@dataclass
class AudioAnalysisResult:
    cough_detected: bool
    breathing_rate: float
    abnormal_sounds: Dict[str, str]
    voice_biomarkers: VoiceBiomarkers
    disease_probs: Dict[str, float]

@dataclass
class FaceROIs:
    forehead: Any
    left_cheek: Any
    right_cheek: Any
    sclera: Any
    conjunctiva: Any
    lips: Any

@dataclass
class ColorBiomarkers:
    jaundice_score: float
    jaundice_severity: str
    pallor_score: float
    cyanosis_score: float
    dengue_flush_score: float

@dataclass
class VisualBiomarkerResult:
    color_biomarkers: ColorBiomarkers
    classifier_scores: Dict[str, float]
    uncertainty_flags: List[str] = field(default_factory=list)

@dataclass
class SenseResult:
    disease_probabilities: Dict[str, float]
    rppg: VitalsResult
    audio: AudioAnalysisResult
    visual: VisualBiomarkerResult
    uncertainty: Dict[str, Tuple[float, float]]
    processing_time_ms: int
