import pytest
import torch
import numpy as np
from ..fusion.cross_modal_fusion import PRISMFusionModel
from ..fusion.fusion_trainer import PRISMFusionTrainer

def test_fusion_output_shape():
    model = PRISMFusionModel(latent_dim=128, num_heads=4)
    rppg = torch.randn(2, 7)
    audio = torch.randn(2, 16)
    visual = torch.randn(2, 11)

    model.eval()
    with torch.no_grad():
        logits = model(rppg, audio, visual)

    assert logits.shape == (2, 12), f"Expected (2,12), got {logits.shape}"
    probs = torch.sigmoid(logits)
    assert (probs >= 0).all() and (probs <= 1).all()

def test_fusion_missing_modality():
    """Missing modality should not crash; output should still be valid."""
    model = PRISMFusionModel()
    rppg = torch.randn(1, 7)
    audio = torch.randn(1, 16)
    visual = torch.randn(1, 11)
    mask = torch.tensor([[False, True, False]])  # audio missing

    model.eval()
    with torch.no_grad():
        logits = model(rppg, audio, visual, modality_mask=mask)

    assert logits.shape == (1, 12)
    assert not torch.isnan(logits).any()

def test_mc_dropout_uncertainty():
    model = PRISMFusionModel()
    rppg = torch.randn(1, 7)
    audio = torch.randn(1, 16)
    visual = torch.randn(1, 11)

    mean_probs, std_probs = model.predict_with_uncertainty(rppg, audio, visual, n_passes=10)
    assert mean_probs.shape == (1, 12)
    assert std_probs.shape == (1, 12)
    assert (mean_probs >= 0).all() and (mean_probs <= 1).all()
    # Std should be non-negative
    assert (std_probs >= 0).all()

def test_fusion_training_smoke():
    model = PRISMFusionModel()
    trainer = PRISMFusionTrainer(model, lr=1e-3)
    loss = trainer.train_epoch(n_batches=5, batch_size=8)
    assert loss > 0  # Loss should be a positive number
    assert not np.isnan(loss)

def test_fusion_beats_random():
    """After a few epochs of training, fusion output should differ from uniform."""
    model = PRISMFusionModel()
    trainer = PRISMFusionTrainer(model, lr=1e-3)
    trainer.train(epochs=3, n_batches=10, batch_size=16)

    rppg, audio, visual, labels = trainer.generate_synthetic_data(4)
    model.eval()
    with torch.no_grad():
        logits = model(rppg, audio, visual)
    probs = torch.sigmoid(logits).numpy()

    # Trained model output should not be all ~0.5 (uniform)
    assert np.std(probs) > 0.01, "Model predictions are too uniform after training"
