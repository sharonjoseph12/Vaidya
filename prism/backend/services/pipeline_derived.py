"""
Layer 2–4 outputs derived from Layer 1 ``sense_results`` and patient context.

Used for evaluation demos and development where full causal / twin / RL
checkpoints are not wired yet: every scalar is computed from sense
probabilities and optional ``patient_features``, not from static JSON.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Optional, Tuple


def _top_diseases(probs: Dict[str, Any], k: int = 3) -> List[Tuple[str, float]]:
    items: List[Tuple[str, float]] = []
    for name, val in (probs or {}).items():
        try:
            items.append((str(name), float(val)))
        except (TypeError, ValueError):
            continue
    items.sort(key=lambda x: x[1], reverse=True)
    return items[:k]


def _slug(s: str) -> str:
    return re.sub(r"[^0-9a-zA-Z_]+", "_", s).strip("_") or "condition"


def build_causal_results(
    sense_results: Dict[str, Any],
    patient_features: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    features = patient_features or {}
    probs = sense_results.get("disease_probabilities") or {}
    if not probs:
        probs = {"Healthy": 1.0}
    ranked = _top_diseases(probs, 1)
    top_name, top_p = ranked[0]
    h = int(hashlib.sha256(f"{top_name}:{top_p:.6f}".encode()).hexdigest()[:8], 16)
    rng_jitter = 0.005 * (h % 17) / 16.0

    base_keys = ["malnutrition", "poor_ventilation", "prior_infection", "genetic_factors"]
    attrib: Dict[str, float] = {}
    raw_sum = 0.0
    for key in base_keys:
        v = features.get(key)
        w = 0.18
        if isinstance(v, (int, float)):
            w = float(max(0.06, min(0.42, abs(float(v)) * 0.12 + 0.12)))
        attrib[key] = w
        raw_sum += w

    severity = min(1.0, max(0.0, top_p))
    for key in attrib:
        attrib[key] = (attrib[key] / max(raw_sum, 1e-6)) * (0.45 + 0.55 * severity) + rng_jitter

    s = sum(attrib.values()) or 1.0
    attrib = {k: round(v / s, 4) for k, v in attrib.items()}

    narrative = (
        f"Causal summary (data-driven): strongest model signal is {top_name} "
        f"({top_p:.1%}). Factor weights are scaled from patient context fields when numeric."
    )

    cf_new = max(0.05, min(top_p * 0.55, top_p - 0.08))
    counterfactuals = [
        {
            "changes": {"malnutrition": ["Severe", "Normal"]},
            "original_probability": round(top_p, 4),
            "new_probability": round(cf_new, 4),
            "feasibility_score": round(0.62 + 0.2 * severity, 4),
        }
    ]

    return {
        "attributions": attrib,
        "narrative": narrative,
        "counterfactuals": counterfactuals,
    }


def build_twin_trajectory(
    sense_results: Dict[str, Any],
    causal_results: Dict[str, Any],
    patient_features: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    probs = sense_results.get("disease_probabilities") or {}
    ranked = _top_diseases(probs, 1)
    top_name, top_p = ranked[0] if ranked else ("Healthy", 0.5)
    tb_prob = float(probs.get("TB", 0.0))
    track_p = max(tb_prob, top_p if top_name != "Healthy" else tb_prob)

    months_crit = max(2.5, min(8.5, 4.0 + 6.0 * (1.0 - min(1.0, track_p))))
    months_interv = months_crit + max(6.0, 14.0 * min(1.0, track_p))

    def traj(months: List[int], slope: float) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        base = min(0.97, max(0.04, track_p))
        for m in months:
            if slope > 0:
                val = min(0.98, base + (m / 6.0) * slope * (1.0 - base))
            else:
                val = max(0.05, base + (m / 6.0) * slope * base)
            out.append(
                {
                    "month": m,
                    "values": {
                        "tb_prob": round(val, 4),
                        "lead_disease": top_name,
                        "lead_prob": round(top_p, 4),
                    },
                }
            )
        return out

    slope_bad = 0.12 if track_p > 0.25 else 0.04
    slope_good = -0.14 if track_p > 0.25 else -0.06

    return {
        "months_to_critical": round(months_crit, 1),
        "months_to_critical_with_intervention": round(months_interv, 1),
        "intervention_applied": "Modality_guided_support_plan",
        "without_intervention": traj([0, 3, 6], slope_bad),
        "with_best_intervention": traj([0, 3, 6], slope_good),
    }


def build_intervention_plan(
    sense_results: Dict[str, Any],
    causal_results: Dict[str, Any],
    twin_trajectory: Dict[str, Any],
    patient_features: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    pf = patient_features or {}
    probs = sense_results.get("disease_probabilities") or {}
    ranked = _top_diseases(probs, 1)
    top_name, top_p = ranked[0] if ranked else ("Healthy", 0.5)
    months = float(twin_trajectory.get("months_to_critical") or 5.0)
    urgency = min(1.0, max(0.0, top_p) * (12.0 / max(months, 1.0)))
    base_qaly = 1.7 + 1.5 * urgency

    dist = 2.5
    dkm = pf.get("nearest_facility_km")
    if isinstance(dkm, (int, float)):
        dist = float(dkm)

    slug = _slug(top_name)
    rec = {
        "rank": 1,
        "intervention": f"Clinical_follow_up_{slug}",
        "description": (
            f"Escalate evaluation when sense layer highlights {top_name} at {top_p:.0%}; "
            "triage per local clinical protocols."
        ),
        "cost_private": int(280 + 450 * urgency),
        "cost_govt": 0,
        "qaly_gain": round(base_qaly, 2),
        "time_to_effect_days": int(18 + 16 * (1.0 - urgency)),
        "side_effect_risk": round(0.03 + 0.07 * urgency, 3),
        "scheme": "Primary_care_pathway",
        "nearest_facility": {
            "name": str(pf.get("nearest_facility_name", "Primary_Health_Center")),
            "distance_km": round(dist, 1),
        },
    }

    pareto = [
        {"cost": 0, "qaly_gain": round(base_qaly * 0.86, 2), "risk": round(0.05 + 0.10 * urgency, 3), "label": "Public_sector_pathway"},
        {"cost": int(750 + 650 * urgency), "qaly_gain": round(base_qaly * 1.12, 2), "risk": round(0.12 + 0.15 * urgency, 3), "label": "Private_specialist"},
        {"cost": int(180 + 280 * urgency), "qaly_gain": round(base_qaly * 0.94, 2), "risk": round(0.07 + 0.10 * urgency, 3), "label": "NGO_supported_care"},
    ]

    return {"recommendations": [rec], "pareto_options": pareto}
