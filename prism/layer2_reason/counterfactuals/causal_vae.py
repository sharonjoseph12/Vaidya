"""T044 & T045 - CausalVAE implementation."""
from __future__ import annotations

import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
except ImportError:
    logger.warning("PyTorch not found. CausalVAE will not be functional.")
    torch = None
    nn = object
    F = None


class CausalVAE(nn.Module if torch else object):
    """
    Causal Variational Autoencoder.
    Learns a DAG over the latent representation.
    """

    def __init__(self, input_dim: int = 15, latent_dim: int = 8, hidden_dim: int = 128):
        super().__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        
        if not torch:
            return
            
        # Encoder
        self.enc_hidden = nn.Linear(input_dim, hidden_dim)
        self.enc_mu = nn.Linear(hidden_dim, latent_dim)
        self.enc_logvar = nn.Linear(hidden_dim, latent_dim)
        
        # Causal adjacency matrix (DAG constraint applied via loss)
        # Initialize as zero matrix
        self.causal_mask = nn.Parameter(torch.zeros(latent_dim, latent_dim))
        
        # Decoder
        self.dec_hidden = nn.Linear(latent_dim, hidden_dim)
        self.dec_out = nn.Linear(hidden_dim, input_dim)
        
    def encode(self, x: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor"]:
        h = F.relu(self.enc_hidden(x))
        return self.enc_mu(h), self.enc_logvar(h)
        
    def reparameterize(self, mu: "torch.Tensor", logvar: "torch.Tensor") -> "torch.Tensor":
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
        
    def causal_forward(self, z_ind: "torch.Tensor") -> "torch.Tensor":
        """
        z_causal = z_ind + z_causal * A
        z_causal (I - A) = z_ind
        z_causal = z_ind @ (I - A)^-1
        """
        I = torch.eye(self.latent_dim, device=z_ind.device)
        # Avoid singular matrix by ensuring diagonal is zero (A has zeros on diag)
        A = self.causal_mask - torch.diag(torch.diag(self.causal_mask))
        
        # torch.linalg.solve computes X where A * X = B
        # Here we want z_causal * (I - A) = z_ind
        # So (I - A)^T * z_causal^T = z_ind^T
        # z_causal^T = solve((I - A)^T, z_ind^T)
        
        M = (I - A).t()
        # Batched solve:
        # M is [latent, latent], z_ind is [batch, latent]
        # We need to solve M * x = b  --> M * z_causal^T = z_ind^T
        z_causal_t = torch.linalg.solve(M, z_ind.t())
        return z_causal_t.t()

    def do_intervention(self, x: "torch.Tensor", interventions: Dict[int, float]) -> "torch.Tensor":
        """Perform do-intervention on latent factors and decode."""
        mu, _ = self.encode(x)
        # Direct intervention on the independent latents before causal mixing
        z_ind = mu.clone()
        for idx, val in interventions.items():
            z_ind[:, idx] = val
            
        z_causal = self.causal_forward(z_ind)
        return self.decode(z_causal)

    def decode(self, z_causal: "torch.Tensor") -> "torch.Tensor":
        h = F.relu(self.dec_hidden(z_causal))
        return self.dec_out(h)

    def forward(self, x: "torch.Tensor") -> Tuple["torch.Tensor", "torch.Tensor", "torch.Tensor", "torch.Tensor"]:
        mu, logvar = self.encode(x)
        z_ind = self.reparameterize(mu, logvar)
        z_causal = self.causal_forward(z_ind)
        x_recon = self.decode(z_causal)
        return x_recon, mu, logvar, z_causal


def causal_vae_loss(
    x_recon: "torch.Tensor",
    x: "torch.Tensor",
    mu: "torch.Tensor",
    logvar: "torch.Tensor",
    causal_mask: "torch.Tensor",
    beta: float = 4.0,
    lambda_dag: float = 1.0,
) -> Tuple["torch.Tensor", Dict[str, float]]:
    """Compute VAE loss with NOTEARS DAG penalty."""
    if not torch:
        return 0.0, {}

    # 1. Reconstruction Loss (MSE)
    recon_loss = F.mse_loss(x_recon, x, reduction="sum") / x.size(0)
    
    # 2. KL Divergence
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp()) / x.size(0)
    
    # 3. NOTEARS DAG Penalty: h(A) = tr(e^{A * A}) - d
    A = causal_mask - torch.diag(torch.diag(causal_mask))
    A_sq = A * A
    
    # Matrix exponential is tr(expm(A_sq)) - d
    # For speed in MVP, we can use a Taylor approximation or torch.matrix_exp
    E = torch.matrix_exp(A_sq)
    h_A = torch.trace(E) - A.size(0)
    
    loss = recon_loss + beta * kl_loss + lambda_dag * h_A
    
    metrics = {
        "loss": loss.item(),
        "recon_loss": recon_loss.item(),
        "kl_loss": kl_loss.item(),
        "h_A": h_A.item(),
    }
    
    return loss, metrics
