from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

@dataclass
class PatientLatentState:
    """
    Represents the compressed physiological state of a patient at a specific time.
    """
    patient_id: str
    z_vector: List[float]  # Latent mean vector
    z_logvar: List[float]  # Latent uncertainty
    last_observation_time: datetime
    organ_specialization: str  # e.g., 'cardiopulmonary', 'metabolic'

@dataclass
class TrajectoryPrediction:
    """
    Represents a projected health trajectory over time.
    """
    patient_id: str
    time_points: List[float]
    predicted_mean: List[List[float]]  # Shape: [num_time_points, num_biomarkers]
    predicted_uncertainty: List[List[float]]
    confidence_interval: List[tuple]
