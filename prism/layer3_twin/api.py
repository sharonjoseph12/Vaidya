"""
API for the Digital Twin service.
Implements the predict_trajectory contract.
"""
from typing import Dict, List
import torch
from .data_models import TrajectoryPrediction
from .causal.intervene import CausalIntervention

class TwinPredictorService:
    def __init__(self, twin_model):
        self.model = twin_model
        # Put model in eval mode
        self.model.eval()
        self.causal_engine = CausalIntervention()

    def predict_trajectory(self, patient_id: str, observations: Dict[str, float], 
                           obs_timestamps: List[float], horizon_days: int = 30) -> TrajectoryPrediction:
        """
        Predict future health trajectory based on current observations.
        """
        # Convert dictionary observations to tensor (dummy implementation)
        # In a real scenario, this involves mapping dict keys to feature indices
        input_dim = self.model.encoder.rnn_cell.input_size
        seq_len = len(obs_timestamps)
        
        # Shape: (batch=1, seq_len, input_dim)
        obs_tensor = torch.zeros(1, seq_len, input_dim) 
        
        # Create target times array (e.g., daily predictions)
        target_times = torch.linspace(0, horizon_days, steps=horizon_days)
        
        with torch.no_grad():
            pred_x, mean, logvar = self.model(obs_tensor, obs_timestamps, target_times)
            
        # Extract mean predictions
        pred_mean = pred_x[0].numpy().tolist() # Convert from (T, D) tensor
        
        return TrajectoryPrediction(
            patient_id=patient_id,
            time_points=target_times.numpy().tolist(),
            predicted_mean=pred_mean,
            predicted_uncertainty=[], # Simplified for now
            confidence_interval=[]
        )

    def simulate_intervention(self, patient_id: str, current_z: List[float], 
                              action_id: int, horizon_days: int = 30) -> Dict:
        """
        Simulate the counterfactual trajectory if a specific intervention is taken.
        """
        z_tensor = torch.tensor([current_z], dtype=torch.float32)
        
        # 1. Apply causal forcing function to latent state
        z_prime = self.causal_engine.apply_intervention(z_tensor, action_id)
        
        # 2. Project forward using ODE
        target_times = torch.linspace(0, horizon_days, steps=horizon_days)
        
        with torch.no_grad():
            from torchdiffeq import odeint_adjoint as odeint
            pred_z = odeint(self.model.ode_func, z_prime, target_times, method='dopri5')
            assert isinstance(pred_z, torch.Tensor)
            pred_z = pred_z.permute(1, 0, 2)
            pred_x = self.model.decoder(pred_z)
            
        counterfactual_mean = pred_x[0].numpy().tolist()
        
        # Dummy QALY calculation for the API return
        qaly_impact = 0.05 * action_id # Mock value
        
        return {
            "patient_id": patient_id,
            "intervention_id": action_id,
            "counterfactual_trajectory": counterfactual_mean,
            "qaly_impact": qaly_impact
        }
