import torch
import torch.nn as nn
from torchdiffeq import odeint_adjoint as odeint
from .ode_func import ODEFunc
from .encoder import ODERNNEncoder

class PatientLatentODE(nn.Module):
    """
    Complete Digital Twin model combining the ODE-RNN encoder, Latent ODE dynamics,
    and the decoder to project future health states.
    """
    def __init__(self, input_dim, latent_dim, hidden_dim, output_dim):
        super(PatientLatentODE, self).__init__()
        self.encoder = ODERNNEncoder(input_dim, hidden_dim, latent_dim)
        self.ode_func = ODEFunc(latent_dim, hidden_dim)
        
        # Maps latent state back to observation space (biomarkers)
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, output_dim)
        )
        
    def reparameterize(self, mean, logvar):
        """Sample from the latent distribution (z_0 ~ N(mean, var))."""
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mean + eps * std

    def forward(self, observations, obs_times, target_times):
        """
        Args:
            observations: Tensor of shape (batch_size, seq_len, input_dim)
            obs_times: Timestamps of observations (not used in basic encoder, but needed for generalized case)
            target_times: Timestamps to predict (e.g., future trajectory)
            
        Returns:
            pred_x: Predicted biomarker values at target_times
            mean, logvar: Latent distribution parameters (for KL divergence loss)
        """
        # 1. Encode irregular observations into initial latent state distribution
        mean, logvar = self.encoder(observations, obs_times)
        
        # 2. Sample initial latent state z_0
        z0 = self.reparameterize(mean, logvar)
        
        # 3. Solve ODE forward in time to predict future states
        # odeint returns shape: (len(target_times), batch_size, latent_dim)
        pred_z = odeint(self.ode_func, z0, target_times, method='dopri5')
        
        assert isinstance(pred_z, torch.Tensor)
        # 4. Decode latent states to predicted biomarkers
        # Permute to (batch_size, len(target_times), latent_dim)
        pred_z = pred_z.permute(1, 0, 2)
        # Apply decoder to all time steps
        pred_x = self.decoder(pred_z)
        
        return pred_x, mean, logvar
