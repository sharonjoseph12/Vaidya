import torch
import torch.nn as nn

class ODERNNEncoder(nn.Module):
    """
    Encoder that processes irregular time series to produce the initial
    latent state distribution for the Neural ODE.
    """
    def __init__(self, input_dim, hidden_dim, latent_dim):
        super(ODERNNEncoder, self).__init__()
        # GRU processes the observations sequentially
        self.rnn_cell = nn.GRUCell(input_dim, hidden_dim)
        # Linear layer maps hidden state to mean and log-variance of latent space
        self.hidden_to_latent = nn.Linear(hidden_dim, latent_dim * 2)

    def forward(self, observations, times=None):
        """
        Process observations backward in time (standard for Latent ODE).
        observations shape: (batch_size, seq_len, input_dim)
        """
        batch_size = observations.size(0)
        h = torch.zeros(batch_size, self.rnn_cell.hidden_size).to(observations.device)
        
        # Traverse sequence in reverse order
        for t in reversed(range(observations.size(1))):
            obs_t = observations[:, t, :]
            h = self.rnn_cell(obs_t, h)
        
        latent_params = self.hidden_to_latent(h)
        mean, logvar = torch.chunk(latent_params, 2, dim=-1)
        return mean, logvar
