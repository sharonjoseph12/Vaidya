import pytest
import torch
from layer3_twin.latent_ode.encoder import ODERNNEncoder
from layer3_twin.latent_ode.ode_func import ODEFunc
from layer3_twin.latent_ode.latent_ode_model import PatientLatentODE

def test_encoder_output_shape():
    batch_size = 2
    seq_len = 5
    input_dim = 3
    latent_dim = 16
    hidden_dim = 32
    
    encoder = ODERNNEncoder(input_dim, hidden_dim, latent_dim)
    obs = torch.randn(batch_size, seq_len, input_dim)
    
    mean, logvar = encoder(obs)
    
    assert mean.shape == (batch_size, latent_dim)
    assert logvar.shape == (batch_size, latent_dim)

def test_ode_model_forward():
    batch_size = 2
    seq_len = 5
    input_dim = 3
    latent_dim = 16
    hidden_dim = 32
    output_dim = 3
    target_len = 10
    
    model = PatientLatentODE(input_dim, latent_dim, hidden_dim, output_dim)
    
    obs = torch.randn(batch_size, seq_len, input_dim)
    obs_times = torch.linspace(0, 5, steps=seq_len)
    target_times = torch.linspace(0, 10, steps=target_len)
    
    pred_x, mean, logvar = model(obs, obs_times, target_times)
    
    assert pred_x.shape == (batch_size, target_len, output_dim)
