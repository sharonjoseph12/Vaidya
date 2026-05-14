"""
Causal integration for the Digital Twin.
Interventions modify the latent state or the ODE dynamics as forcing functions.
"""
import torch

class CausalIntervention:
    """
    Applies interventions from Layer 2 (Causal Engine) to Layer 3 (Digital Twin).
    """
    def __init__(self, causal_graph=None):
        self.causal_graph = causal_graph # Reference to SCM from Layer 2

    def apply_intervention(self, z_state, action_id):
        """
        Modify the latent state z to reflect an immediate intervention effect.
        In a full SCM, this would update z based on structural equations.
        Here we use a simplified mock effect matrix.
        """
        # Ensure z_state is a tensor
        if not isinstance(z_state, torch.Tensor):
            z_state = torch.tensor(z_state, dtype=torch.float32)
            
        # Mock causal effect: action 1 improves feature 0 by 10%
        # action 2 improves feature 1 by 20%, etc.
        z_prime = z_state.clone()
        
        # Simplified deterministic effect for the prototype
        if action_id == 1:
            z_prime[..., 0] = z_prime[..., 0] * 0.9
        elif action_id == 2:
            z_prime[..., 1] = z_prime[..., 1] * 0.8
        elif action_id == 3:
            z_prime[..., 2] = z_prime[..., 2] * 0.7
            
        return z_prime
