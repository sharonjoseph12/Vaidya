from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import json

@dataclass
class VitalsResult:
    hr: float
    spo2: float
    hrv_rmssd: float
    hrv_sdnn: float
    lf_hf_ratio: float
    rr: float
    confidence_scores: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VitalsResult":
        return cls(**d)

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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VoiceBiomarkers":
        return cls(**d)

@dataclass
class AudioAnalysisResult:
    cough_detected: bool
    breathing_rate: float
    abnormal_sounds: Dict[str, str]
    voice_biomarkers: VoiceBiomarkers
    disease_probs: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AudioAnalysisResult":
        d["voice_biomarkers"] = VoiceBiomarkers.from_dict(d["voice_biomarkers"])
        return cls(**d)

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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ColorBiomarkers":
        return cls(**d)

@dataclass
class VisualBiomarkerResult:
    color_biomarkers: ColorBiomarkers
    classifier_scores: Dict[str, float]
    uncertainty_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VisualBiomarkerResult":
        d["color_biomarkers"] = ColorBiomarkers.from_dict(d["color_biomarkers"])
        return cls(**d)

@dataclass
class SenseResult:
    disease_probabilities: Dict[str, float]
    rppg: VitalsResult
    audio: AudioAnalysisResult
    visual: VisualBiomarkerResult
    uncertainty: Dict[str, Tuple[float, float]]
    processing_time_ms: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "disease_probabilities": self.disease_probabilities,
            "rppg": self.rppg.to_dict(),
            "audio": self.audio.to_dict(),
            "visual": self.visual.to_dict(),
            "uncertainty": {k: list(v) for k, v in self.uncertainty.items()},
            "processing_time_ms": self.processing_time_ms,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SenseResult":
        return cls(
            disease_probabilities=d["disease_probabilities"],
            rppg=VitalsResult.from_dict(d["rppg"]),
            audio=AudioAnalysisResult.from_dict(d["audio"]),
            visual=VisualBiomarkerResult.from_dict(d["visual"]),
            uncertainty={k: tuple(v) for k, v in d["uncertainty"].items()},
            processing_time_ms=d["processing_time_ms"],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, s: str) -> "SenseResult":
        return cls.from_dict(json.loads(s))

@dataclass
class PRISMSenseResult:
    disease_probabilities: Dict[str, float]
    uncertainty_bounds: Dict[str, Tuple[float, float]]
    shap_values: Optional[Dict[str, float]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
