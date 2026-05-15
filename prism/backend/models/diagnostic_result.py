"""
PRISM Platform — Diagnostic Result Pydantic Schemas
Defines the data models for all four PRISM layers' outputs.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


# ============================================================
# Layer 1: SENSE Results
# ============================================================

class RPPGResult(BaseModel):
    """Remote photoplethysmography vital signs."""
    hr: float = Field(..., description="Heart rate in BPM")
    spo2: float = Field(..., description="Blood oxygen saturation %")
    hrv_rmssd: float = Field(..., description="HRV RMSSD in ms")
    hrv_sdnn: Optional[float] = None
    lf_hf_ratio: Optional[float] = None
    rr: float = Field(..., description="Respiratory rate breaths/min")
    confidence: Optional[dict[str, float]] = None


class AudioResult(BaseModel):
    """Audio analysis results."""
    cough_detected: bool = False
    cough_count: int = 0
    disease_probs: dict[str, float] = Field(default_factory=dict)
    breathing_rate: Optional[float] = None
    wheeze_detected: bool = False
    crackle_detected: bool = False


class VisualResult(BaseModel):
    """Visual biomarker scores."""
    jaundice_score: float = Field(default=0.0, ge=0.0, le=1.0)
    anemia_score: float = Field(default=0.0, ge=0.0, le=1.0)
    cyanosis_score: float = Field(default=0.0, ge=0.0, le=1.0)
    dengue_flush_score: float = Field(default=0.0, ge=0.0, le=1.0)
    pallor_score: float = Field(default=0.0, ge=0.0, le=1.0)


class IMUResult(BaseModel):
    """Inertial measurement unit gait analysis."""
    gait_symmetry: float = Field(default=0.0, ge=0.0, le=1.0)
    cadence: float = 0.0
    step_variability: float = 0.0


class SenseResult(BaseModel):
    """Complete Layer 1 output."""
    disease_probabilities: dict[str, float] = Field(default_factory=dict)
    rppg: Optional[RPPGResult] = None
    audio: Optional[AudioResult] = None
    visual: Optional[VisualResult] = None
    imu: Optional[IMUResult] = None
    uncertainty: dict[str, list[float]] = Field(default_factory=dict)
    modalities_available: list[str] = Field(default_factory=list)
    processing_time_ms: int = 0


# ============================================================
# Layer 2: REASON Results
# ============================================================

class CounterfactualExplanation(BaseModel):
    """A single counterfactual scenario."""
    changes: dict[str, list] = Field(default_factory=dict)
    new_probability: float = Field(ge=0.0, le=1.0)
    feasibility_score: float = Field(ge=0.0, le=1.0)
    n_features_changed: int = 0


class CausalResult(BaseModel):
    """Complete Layer 2 output."""
    attributions: dict[str, float] = Field(default_factory=dict)
    top_intervention: Optional[str] = None
    intervention_effects: dict[str, float] = Field(default_factory=dict)
    patient_risk_factors: dict[str, float] = Field(default_factory=dict)
    counterfactuals: list[CounterfactualExplanation] = Field(default_factory=list)
    narrative: str = ""
    causal_graph_dot: str = ""


# ============================================================
# Layer 3: PROJECT Results (Digital Twin Trajectory)
# ============================================================

class TrajectoryPoint(BaseModel):
    """A single point in a health trajectory."""
    month: float
    values: dict[str, float] = Field(default_factory=dict)


class TwinTrajectory(BaseModel):
    """Complete Layer 3 output."""
    without_intervention: list[TrajectoryPoint] = Field(default_factory=list)
    with_best_intervention: list[TrajectoryPoint] = Field(default_factory=list)
    confidence_bands: dict[str, list[float]] = Field(default_factory=dict)
    months_to_critical: Optional[float] = None
    months_to_critical_with_intervention: Optional[float] = None
    intervention_applied: Optional[str] = None
    twin_model_version: Optional[str] = None


# ============================================================
# Layer 4: ACT Results (Intervention Plan)
# ============================================================

class InterventionRecommendation(BaseModel):
    """A single intervention option."""
    rank: int
    intervention: str
    description: str = ""
    rationale: str = ""
    cost_govt: float = 0.0
    cost_private: float = 0.0
    qaly_gain: float = 0.0
    cost_per_qaly: float = 0.0
    time_to_effect_days: int = 0
    side_effect_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    nearest_facility: Optional[dict] = None
    scheme: Optional[str] = None


class ParetoOption(BaseModel):
    """A point on the Pareto frontier."""
    label: str
    cost: float
    qaly_gain: float
    risk: float = 0.0


class TestRecommendation(BaseModel):
    """Active uncertainty reduction recommendation."""
    recommended_test: str
    cost: float
    expected_uncertainty_reduction: float
    rationale: str = ""


class InterventionPlan(BaseModel):
    """Complete Layer 4 output."""
    recommendations: list[InterventionRecommendation] = Field(default_factory=list)
    pareto_options: list[ParetoOption] = Field(default_factory=list)
    active_uncertainty_reduction: Optional[TestRecommendation] = None


# ============================================================
# Full Diagnostic Result (all layers combined)
# ============================================================

class FullDiagnosticResult(BaseModel):
    """Complete PRISM diagnostic session result."""
    session_id: UUID
    status: str = "complete"
    primary_diagnosis: Optional[str] = None
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    disease_probabilities: dict[str, float] = Field(default_factory=dict)
    sense_results: Optional[SenseResult] = None
    causal_results: Optional[CausalResult] = None
    twin_trajectory: Optional[TwinTrajectory] = None
    intervention_plan: Optional[InterventionPlan] = None
    uncertainty_bounds: dict[str, list[float]] = Field(default_factory=dict)
    processing_time_ms: int = 0
    model_version: Optional[str] = None
    offline_mode: bool = False

    model_config = {"from_attributes": True}


class AnalysisStartResponse(BaseModel):
    """Response when analysis is queued."""
    session_id: str
    task_id: str
    status: str = "queued"
    estimated_time_seconds: int = 10


class AnalysisProgressEvent(BaseModel):
    """SSE event for pipeline progress."""
    stage: str
    progress: float = Field(ge=0.0, le=1.0)
    message: str = ""
    session_id: Optional[str] = None
