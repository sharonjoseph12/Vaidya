"""
PRISM Platform — Inference Orchestration Service
Chains Layer 1→2→3→4 processing for the full diagnostic pipeline.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any, Optional

from layer2_reason.causal_engine import PRISMCausalEngine
from backend.config import get_settings

logger = logging.getLogger(__name__)


def _sense_dict_shape(sense: Any) -> dict[str, Any]:
    """Normalize Layer 1 output to the dict shape used downstream."""
    if isinstance(sense, dict) and "disease_probabilities" in sense:
        return sense
    if isinstance(sense, dict):
        return {
            "disease_probabilities": sense,
            "rppg": {},
            "audio": {},
            "visual": {},
            "uncertainty": {},
            "modalities_available": [],
        }
    return {
        "disease_probabilities": {},
        "rppg": {},
        "audio": {},
        "visual": {},
        "uncertainty": {},
        "modalities_available": [],
    }


class InferenceService:
    """
    Orchestrates the full PRISM inference pipeline for synchronous callers.

    Layer 1 prefers real ``PRISMSensePipeline`` when local file paths exist;
    layers 2–4 use sense-derived heuristics (see ``pipeline_derived``) until
    trained causal / twin / RL artifacts are wired.
    """

    def __init__(self) -> None:
        self._models_loaded = False

    def load_models(self) -> None:
        """Load lightweight stubs used only when real SENSE is unavailable."""
        from backend.core_ml.model_loader import (
            load_yamnet_model,
        )
        
        # Load actual models
        self.causal_engine_tb = PRISMCausalEngine(
            disease="tb",
            graphs_dir=Path("/app/layer2_reason/graphs/"),
            models_dir=Path("/app/layer2_reason/scm_models/")
        )
        logger.info("Inference models loaded (Layer 2 Integrated)")

        self.sense_model = load_yamnet_model()
        self._models_loaded = True
        logger.info("Inference YAMNet stub loaded (fallback SENSE only)")

    def run_full_pipeline(
        self,
        audio_path: Optional[str] = None,
        video_path: Optional[str] = None,
        patient_features: Optional[dict[str, Any]] = None,
        patient_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Run the complete 4-layer PRISM pipeline.

        Returns dict with keys including sense_results, causal_results,
        twin_trajectory, intervention_plan, disease_probabilities.
        """
        settings = get_settings()
        features = patient_features or {}

        try:
            start = time.time()
            sense = self._run_sense(audio_path, video_path)
            sense_results = _sense_dict_shape(sense)
            probs = sense_results.get("disease_probabilities") or {}

            from backend.services.pipeline_derived import (
                build_causal_results,
                build_intervention_plan,
                build_twin_trajectory,
            )

            causal = build_causal_results(sense_results, features)
            twin = build_twin_trajectory(sense_results, causal, features)
            plan = build_intervention_plan(sense_results, causal, twin, features)

            elapsed_ms = int((time.time() - start) * 1000)
            logger.info("Full pipeline completed in %dms", elapsed_ms)

            primary = max(probs, key=probs.get) if probs else "Unknown"
            unc = sense_results.get("uncertainty") or {}
            uncertainty_bounds = unc if unc else self._uncertainty_from_probs(probs)

            return {
                "sense_results": sense_results,
                "disease_probabilities": probs,
                "uncertainty_bounds": uncertainty_bounds,
                "primary_diagnosis": primary,
                "causal_results": causal,
                "twin_trajectory": twin,
                "intervention_plan": plan,
                "processing_time_ms": elapsed_ms,
            }
        except Exception as e:
            logger.error("Pipeline failed for session %s: %s", session_id, e)
            demo_hint = (patient_id and "demo" in patient_id.lower()) or (
                session_id and "demo" in session_id.lower()
            )
            if demo_hint and settings.allow_demo_hardcode_fallback:
                logger.warning("allow_demo_hardcode_fallback=true: returning static demo payload")
                return _static_demo_payload()
            raise

    @staticmethod
    def _uncertainty_from_probs(probs: dict[str, Any]) -> dict[str, list[float]]:
        out: dict[str, list[float]] = {}
        for k, v in probs.items():
            try:
                p = float(v)
                m = min(0.12, 0.03 + p * 0.2)
                out[str(k)] = [max(0.0, p - m), min(1.0, p + m)]
            except (TypeError, ValueError):
                continue
        return out

    def _run_sense(self, audio_path: Optional[str], video_path: Optional[str]) -> Any:
        """Layer 1 — real pipeline on local files when available."""
        from backend.services.real_sense import try_run_real_sense

        la = str(audio_path) if audio_path and Path(str(audio_path)).is_file() else None
        lv = str(video_path) if video_path and Path(str(video_path)).is_file() else None
        if la or lv:
            real = try_run_real_sense(lv, la)
            if real is not None:
                return real

        if not self._models_loaded:
            self.load_models()
        data = f"{audio_path}_{video_path}"
        infer_results = self.sense_model.infer(data)
        dprobs = {
            "TB": float(infer_results.get("TB_Cough", 0.0)),
            "Pneumonia": float(infer_results.get("Wheezing", 0.0)),
            "Healthy": float(infer_results.get("Normal", 0.1)),
        }
        s = sum(dprobs.values()) or 1.0
        dprobs = {k: v / s for k, v in dprobs.items()}
        return {
            "disease_probabilities": dprobs,
            "rppg": {},
            "audio": {},
            "visual": {},
            "uncertainty": self._uncertainty_from_probs(dprobs),
            "modalities_available": [],
            "processing_time_ms": 0,
        }


def _static_demo_payload() -> dict[str, Any]:
    """Last-resort static payload; only used when allow_demo_hardcode_fallback is true."""
    return {
        "disease_probabilities": {"TB": 0.79, "Anemia": 0.71, "Pneumonia": 0.12, "Healthy": 0.05},
        "uncertainty_bounds": {"TB": [0.70, 0.88], "Anemia": [0.65, 0.78]},
        "primary_diagnosis": "TB",
        "causal_results": {
            "attributions": {
                "malnutrition": 0.38,
                "poor_ventilation": 0.24,
                "prior_infection": 0.21,
                "genetic_factors": 0.17,
            },
            "narrative": "Static demo fallback (enable only for pitch-deck resilience).",
            "counterfactuals": [
                {
                    "changes": {"malnutrition": ["Severe", "Normal"]},
                    "original_probability": 0.79,
                    "new_probability": 0.31,
                    "feasibility_score": 0.85,
                }
            ],
        },
        "twin_trajectory": {
            "months_to_critical": 5.0,
            "months_to_critical_with_intervention": 19.0,
            "intervention_applied": "Nutritional_Supplementation",
            "without_intervention": [
                {"month": 0, "values": {"tb_prob": 0.79}},
                {"month": 3, "values": {"tb_prob": 0.85}},
                {"month": 6, "values": {"tb_prob": 0.92}},
            ],
            "with_best_intervention": [
                {"month": 0, "values": {"tb_prob": 0.79}},
                {"month": 3, "values": {"tb_prob": 0.65}},
                {"month": 6, "values": {"tb_prob": 0.45}},
            ],
        },
        "intervention_plan": {
            "recommendations": [
                {
                    "rank": 1,
                    "intervention": "Nutritional_Supplementation_and_DOTS",
                    "description": "Provide caloric support and initiate DOTS therapy.",
                    "cost_private": 400,
                    "cost_govt": 0,
                    "qaly_gain": 2.5,
                    "time_to_effect_days": 30,
                    "side_effect_risk": 0.05,
                    "scheme": "Nikshay Poshan Yojana",
                    "nearest_facility": {"name": "Primary Health Center", "distance_km": 1.2},
                }
            ],
            "pareto_options": [
                {"cost": 0, "qaly_gain": 2.0, "risk": 0.05, "label": "Free Government Treatment"},
                {"cost": 1400, "qaly_gain": 3.0, "risk": 0.18, "label": "Private Specialist"},
            ],
        },
        "processing_time_ms": 0,
    }


    def _run_reason(self, sense_results, patient_features):
        """Layer 2 — delegates to Person 2's causal engine."""
        # Map sense_results + patient_features to engine input
        # For demo, we use a default disease probability of 0.75 if not provided
        prob = patient_features.get("disease_probability", 0.75)
        
        report = self.causal_engine_tb.full_causal_analysis(
            patient_features=patient_features,
            disease_probability=prob
        )
        
        return {
            "attributions": report.causal_attributions.attributions,
            "narrative": report.narrative,
            "causal_graph_dot": report.causal_graph_dot,
            "counterfactuals": [
                {
                    "changes": cf.changes,
                    "original_probability": prob,
                    "new_probability": cf.new_disease_probability,
                    "feasibility_score": cf.feasibility_score
                } for cf in report.counterfactuals
            ]
        }

    def _run_project(self, sense, causal, features):
        """Layer 3 — delegates to Person 3's digital twin."""
        # TODO: Integrate actual Digital Twin
        return None

    def _run_act(self, sense, causal, twin, features):
        """Layer 4 — delegates to Person 3's RL optimizer."""
        # TODO: Integrate actual RL agent
        return None


# Singleton
inference_service = InferenceService()
