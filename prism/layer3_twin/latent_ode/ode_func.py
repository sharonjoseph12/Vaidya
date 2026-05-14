import torch
import torch.nn as nn

class ODEFunc(nn.Module):
    """
    Neural network defining the continuous-time dynamics of the latent state.
    dy/dt = f_theta(y, t)
    """
    def __init__(self, latent_dim, hidden_dim):
        super(ODEFunc, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.Tanh(),
            nn.Linear(hidden_dim, latent_dim)
        )
        # Initialize weights for smooth, stable ODE integration
        for m in self.net.modules():
            if isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, mean=0, std=0.1)
                nn.init.constant_(m.bias, val=0)

    def forward(self, t, y):
        # We don't explicitly use t in this autonomous ODE
        return self.net(y)
