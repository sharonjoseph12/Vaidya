import time
import torch
import numpy as np
from typing import Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from .rppg.rppg_pipeline import PRISMrPPGPipeline
from .audio.audio_pipeline import PRISMAudioPipeline
from .visual.visual_pipeline import PRISMVisualPipeline
from .fusion.cross_modal_fusion import PRISMFusionModel
from .datatypes import (
    SenseResult, VitalsResult, AudioAnalysisResult,
    VisualBiomarkerResult, ColorBiomarkers, VoiceBiomarkers,
)
from .logger import logger

class PRISMSensePipeline:
    """
    End-to-end SENSE pipeline: orchestrates rPPG + Audio + Visual → Fusion → SenseResult.
    Runs modality pipelines in parallel using ThreadPoolExecutor.
    """

    def __init__(self, fps: int = 30, sample_rate: int = 16000):
        self.rppg = PRISMrPPGPipeline(fps=fps)
        self.audio = PRISMAudioPipeline(sample_rate=sample_rate)
        self.visual = PRISMVisualPipeline()
        self.fusion = PRISMFusionModel()
        self.fusion.eval()

    def run(
        self,
        video_path: Optional[str] = None,
        audio_path: Optional[str] = None,
    ) -> SenseResult:
        """Execute the full SENSE pipeline. Accepts video and/or audio paths.

        Edge cases handled:
            - Missing modalities: masked out during fusion via ``modality_mask``.
            - Low-light video: detected via mean luminance; falls back to audio-only.
            - High-noise audio: detected via SNR estimate; flagged in warnings.
        """
        t_start = time.time()
        rppg_result = None
        audio_result = None
        visual_result = None
        warnings: list[str] = []

        # Quality checks
        low_light = False
        if video_path:
            low_light = self._check_low_light(video_path)
            if low_light:
                warnings.append("low_light_detected: visual/rppg may be unreliable")
                logger.warning("Low-light video detected — visual and rPPG confidence degraded")

        high_noise = False
        if audio_path:
            high_noise = self._check_audio_noise(audio_path)
            if high_noise:
                warnings.append("high_noise_audio: cough classification may be unreliable")
                logger.warning("High background noise detected — audio confidence degraded")

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {}
            if video_path:
                futures["rppg"] = pool.submit(self._safe_rppg, video_path)
                futures["visual"] = pool.submit(self._safe_visual, video_path)
            if audio_path:
                futures["audio"] = pool.submit(self._safe_audio, audio_path)

            for key, future in futures.items():
                try:
                    result = future.result(timeout=30)
                    if key == "rppg":
                        rppg_result = result
                    elif key == "audio":
                        audio_result = result
                    elif key == "visual":
                        visual_result = result
                except Exception as e:
                    logger.error(f"{key} pipeline failed: {e}")
                    warnings.append(f"{key}_pipeline_error: {e}")

        # Defaults for missing modalities
        if rppg_result is None:
            rppg_result = VitalsResult(0, 98, 0, 0, 1.0, 16, {})
        if audio_result is None:
            audio_result = AudioAnalysisResult(False, 0, {}, VoiceBiomarkers(0, 0, 0), {})
        if visual_result is None:
            visual_result = VisualBiomarkerResult(
                ColorBiomarkers(0, "none", 0, 0, 0), {}, ["no_video"]
            )

        # Featurize for fusion
        rppg_feat = self._rppg_to_tensor(rppg_result)
        audio_feat = self._audio_to_tensor(audio_result)
        visual_feat = self._visual_to_tensor(visual_result)

        # Build modality mask (True = missing/unreliable)
        mask = torch.tensor([[
            video_path is None or low_light,   # rppg missing or degraded
            audio_path is None,                # audio missing
            video_path is None or low_light,   # visual missing or degraded
        ]])

        # Fusion inference with uncertainty
        mean_probs, std_probs = self.fusion.predict_with_uncertainty(
            rppg_feat, audio_feat, visual_feat,
            modality_mask=mask, n_passes=20,
        )

        disease_probs = {
            name: float(mean_probs[0, i])
            for i, name in enumerate(PRISMFusionModel.DISEASES)
        }
        uncertainty = {
            name: (float(mean_probs[0, i]), float(std_probs[0, i]))
            for i, name in enumerate(PRISMFusionModel.DISEASES)
        }

        elapsed_ms = int((time.time() - t_start) * 1000)
        logger.info(f"SENSE pipeline completed in {elapsed_ms}ms")

        return SenseResult(
            disease_probabilities=disease_probs,
            rppg=rppg_result,
            audio=audio_result,
            visual=visual_result,
            uncertainty=uncertainty,
            processing_time_ms=elapsed_ms,
        )

    # ---- Safe wrappers ----
    def _safe_rppg(self, video_path: str) -> Optional[VitalsResult]:
        try:
            return self.rppg.process_video(video_path)
        except Exception as e:
            logger.error(f"rPPG error: {e}")
            return None

    def _safe_audio(self, audio_path: str) -> Optional[AudioAnalysisResult]:
        try:
            return self.audio.full_analysis(audio_path)
        except Exception as e:
            logger.error(f"Audio error: {e}")
            return None

    def _safe_visual(self, video_path: str) -> Optional[VisualBiomarkerResult]:
        try:
            return self.visual.analyze_video(video_path)
        except Exception as e:
            logger.error(f"Visual error: {e}")
            return None

    # ---- Feature extraction helpers ----
    def _rppg_to_tensor(self, v: VitalsResult) -> torch.Tensor:
        return torch.tensor([[
            v.hr, v.spo2, v.hrv_rmssd, v.hrv_sdnn,
            v.lf_hf_ratio, v.rr,
            v.confidence_scores.get("hr_snr", 0.0),
        ]], dtype=torch.float32)

    def _audio_to_tensor(self, a: AudioAnalysisResult) -> torch.Tensor:
        probs = [a.disease_probs.get(d, 0.0) for d in
                 ["TB", "COVID", "Pneumonia", "Whooping_Cough", "Asthma", "COPD", "Healthy", "Jaundice"]]
        extras = [
            a.breathing_rate,
            a.voice_biomarkers.jitter,
            a.voice_biomarkers.shimmer,
            a.voice_biomarkers.hnr,
            1.0 if a.cough_detected else 0.0,
            0.0, 0.0, 0.0,  # padding to 16
        ]
        return torch.tensor([probs + extras], dtype=torch.float32)

    def _visual_to_tensor(self, v: VisualBiomarkerResult) -> torch.Tensor:
        cb = v.color_biomarkers
        cs = v.classifier_scores
        return torch.tensor([[
            cb.jaundice_score, cb.pallor_score, cb.cyanosis_score, cb.dengue_flush_score,
            cs.get("anemia", 0.0), cs.get("cyanosis", 0.0), cs.get("dengue", 0.0),
            cs.get("jaundice_none", 0.0), cs.get("jaundice_mild", 0.0),
            cs.get("jaundice_moderate", 0.0), cs.get("jaundice_severe", 0.0),
        ]], dtype=torch.float32)

    # ---- Quality checks ----
    @staticmethod
    def _check_low_light(video_path: str, threshold: float = 40.0) -> bool:
        """Check if first frame mean luminance is below threshold.

        Args:
            video_path: Path to video file.
            threshold: Mean Y-channel value below which the frame is
                considered low-light. Default 40 (out of 255).

        Returns:
            ``True`` if the video is too dark for reliable visual analysis.
        """
        import cv2
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return True
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return float(np.mean(gray)) < threshold

    @staticmethod
    def _check_audio_noise(audio_path: str, snr_threshold: float = 5.0) -> bool:
        """Estimate SNR and flag high-noise recordings.

        Uses a simple energy-ratio heuristic: segments with energy above the
        median are treated as signal, the rest as noise.

        Args:
            audio_path: Path to audio file.
            snr_threshold: Minimum acceptable SNR in dB. Default 5.0.

        Returns:
            ``True`` if estimated SNR is below threshold.
        """
        import librosa
        try:
            y, sr = librosa.load(audio_path, sr=16000, duration=10)
        except Exception:
            return True

        if len(y) == 0:
            return True

        rms = librosa.feature.rms(y=y, hop_length=512)[0]
        median_rms = np.median(rms)

        signal_energy = np.mean(rms[rms > median_rms] ** 2)
        noise_energy = np.mean(rms[rms <= median_rms] ** 2) + 1e-10
        snr_db = 10 * np.log10(signal_energy / noise_energy)

        return float(snr_db) < snr_threshold
