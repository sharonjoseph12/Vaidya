"""T032 - Tests for diverse counterfactual generation (US2)."""
from __future__ import annotations

import pandas as pd
import pytest

from layer2_reason.causal_engine import CounterfactualExplanation
from layer2_reason.counterfactuals.counterfactual_ranker import rank_counterfactuals
from layer2_reason.counterfactuals.dice_generator import compute_feasibility, generate_counterfactuals


@pytest.fixture
def mock_reference_data():
    return pd.DataFrame({
        "nutrition_score": [1.0, 2.0, 8.0, 9.0, 5.0] * 3,
        "bmi": [16.0, 18.0, 22.0, 25.0, 20.0] * 3,
        "crowding_index": [4.0, 3.0, 1.0, 0.5, 2.0] * 3,
        "disease_prob": [0.8, 0.6, 0.1, 0.05, 0.4] * 3,
    })


def test_compute_feasibility():
    # Only nutrition changed
    changes = {"nutrition_score": (3.0, 8.0)}
    f_score = compute_feasibility(changes)
    assert 0.0 < f_score < 1.0
    
    # Nutrition + Crowding (weight 0.9 vs 0.2)
    f_score_2 = compute_feasibility({"nutrition_score": (3.0, 8.0), "crowding_index": (4.0, 1.0)})
    assert f_score_2 < f_score  # average of 0.9 and 0.2 weights is lower than 0.9 alone


def test_mock_dice_generator(mock_reference_data):
    patient = {"nutrition_score": 4.0, "bmi": 18.0, "crowding_index": 3.0}
    cfs = generate_counterfactuals(
        patient_data=patient,
        disease_model=None,
        features_list=list(patient.keys()),
        reference_data=mock_reference_data,
        n_cf=3,
    )
    
    assert len(cfs) == 3
    assert all(isinstance(cf, CounterfactualExplanation) for cf in cfs)
    assert all(cf.probability_reduction > 0 for cf in cfs)
    assert all(cf.n_features_changed == 1 for cf in cfs)


def test_counterfactual_ranker():
    cfs = [
        CounterfactualExplanation(
            changes={"nutrition_score": (3, 8)},
            new_disease_probability=0.2,
            probability_reduction=0.6, # High impact
            n_features_changed=1,
            feasibility_score=0.8, # High feasibility
            rank=0
        ),
        CounterfactualExplanation(
            changes={"nutrition_score": (3, 8), "bmi": (16, 20)},
            new_disease_probability=0.1,
            probability_reduction=0.7, # Higher impact
            n_features_changed=2, # More changes = lower score
            feasibility_score=0.5, # Lower feasibility
            rank=0
        )
    ]
    
    ranked = rank_counterfactuals(cfs)
    
    # CF 0 should win because 1 change and higher feasibility (0.5*0.8 + 0.3*0.6 + 0.2/1 = 0.4 + 0.18 + 0.2 = 0.78)
    # vs CF 1 (0.5*0.5 + 0.3*0.7 + 0.2/2 = 0.25 + 0.21 + 0.1 = 0.56)
    assert ranked[0].changes == {"nutrition_score": (3, 8)}
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2


class TestCausalVAE:
    def test_causal_vae_forward_shapes(self):
        try:
            import torch
        except ImportError:
            pytest.skip("PyTorch not installed")
            
        from layer2_reason.counterfactuals.causal_vae import CausalVAE, causal_vae_loss
        
        vae = CausalVAE(input_dim=15, latent_dim=8)
        x = torch.randn(10, 15)
        x_recon, mu, logvar, z_causal = vae(x)
        
        assert x_recon.shape == (10, 15)
        assert mu.shape == (10, 8)
        assert z_causal.shape == (10, 8)
        
        # Test loss
        loss, metrics = causal_vae_loss(x_recon, x, mu, logvar, vae.causal_mask)
        assert loss.item() >= 0
        assert metrics["h_A"] >= 0
        
    def test_do_intervention_shape(self):
        try:
            import torch
        except ImportError:
            pytest.skip("PyTorch not installed")
            
        from layer2_reason.counterfactuals.causal_vae import CausalVAE
        vae = CausalVAE(input_dim=15, latent_dim=8)
        x = torch.randn(5, 15)
        
        out = vae.do_intervention(x, {0: 5.0})
        assert out.shape == (5, 15)
