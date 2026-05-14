import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Tuple
from .cross_modal_fusion import PRISMFusionModel
from ..logger import logger

class PRISMFusionTrainer:
    """Training loop for the cross-modal fusion model with synthetic data generation."""

    def __init__(self, model: PRISMFusionModel, lr: float = 1e-3):
        self.model = model
        self.optimizer = optim.Adam(model.parameters(), lr=lr)
        self.criterion = nn.BCEWithLogitsLoss()

    @staticmethod
    def generate_synthetic_data(batch_size: int = 32) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """Generate synthetic training data for development / smoke testing."""
        rppg = torch.randn(batch_size, 7)     # HR, SpO2, HRV×3, RR, confidence
        audio = torch.randn(batch_size, 16)   # cough probs (8) + breathing_rate + voice (3) + spectral (4)
        visual = torch.randn(batch_size, 11)  # jaundice(4) + anemia + cyanosis + dengue + pallor + flush + 2 spare
        labels = (torch.rand(batch_size, 12) > 0.7).float()  # multi-label binary
        return rppg, audio, visual, labels

    def train_epoch(self, n_batches: int = 50, batch_size: int = 32) -> float:
        self.model.train()
        total_loss = 0.0

        for _ in range(n_batches):
            rppg, audio, visual, labels = self.generate_synthetic_data(batch_size)
            self.optimizer.zero_grad()
            logits = self.model(rppg, audio, visual)
            loss = self.criterion(logits, labels)
            loss.backward()
            self.optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / n_batches
        return avg_loss

    def train(self, epochs: int = 10, n_batches: int = 50, batch_size: int = 32):
        for epoch in range(epochs):
            loss = self.train_epoch(n_batches, batch_size)
            logger.info(f"Epoch {epoch+1}/{epochs} — Loss: {loss:.4f}")

    def calibrate_temperature(self, val_rppg, val_audio, val_visual, val_labels, lr=0.01, max_iter=50):
        """Temperature scaling for post-hoc calibration."""
        temperature = nn.Parameter(torch.ones(1) * 1.5)
        optimizer = optim.LBFGS([temperature], lr=lr, max_iter=max_iter)
        nll = nn.BCEWithLogitsLoss()

        self.model.eval()
        with torch.no_grad():
            logits = self.model(val_rppg, val_audio, val_visual)

        def closure():
            optimizer.zero_grad()
            loss = nll(logits / temperature, val_labels)
            loss.backward()
            return loss

        optimizer.step(closure)
        return temperature.item()
