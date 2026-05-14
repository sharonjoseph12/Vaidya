"""
PRISM Platform — Differential Privacy Utilities
Noise calibration, sensitivity calculation, and privacy budget tracking.
"""
import numpy as np
import logging

logger = logging.getLogger(__name__)


def calibrate_noise_std(epsilon: float, delta: float, sensitivity: float = 2.0) -> float:
    """Calibrate Gaussian noise std for (epsilon, delta)-DP."""
    return sensitivity * np.sqrt(2 * np.log(1.25 / delta)) / epsilon


def add_gaussian_noise(weights: list, epsilon: float, delta: float, sensitivity: float = 2.0) -> list:
    """Add calibrated Gaussian noise to model weights for DP."""
    noise_std = calibrate_noise_std(epsilon, delta, sensitivity)
    return [np.array(w) + np.random.normal(0, noise_std, np.array(w).shape) for w in weights]


def clip_gradient_norm(gradients: list, max_norm: float = 1.0) -> list:
    """Clip gradient L2 norm to bound sensitivity."""
    total_norm = np.sqrt(sum(np.sum(g**2) for g in gradients))
    if total_norm > max_norm:
        scale = max_norm / total_norm
        return [g * scale for g in gradients]
    return gradients


class PrivacyBudgetTracker:
    """Track cumulative privacy budget spent across FL rounds."""

    def __init__(self, total_epsilon: float = 10.0, total_delta: float = 1e-4):
        self.total_epsilon = total_epsilon
        self.total_delta = total_delta
        self.spent_epsilon = 0.0
        self.spent_delta = 0.0
        self.rounds = 0

    def spend(self, epsilon: float, delta: float) -> bool:
        """Record privacy spend. Returns False if budget exceeded."""
        if self.spent_epsilon + epsilon > self.total_epsilon:
            logger.warning("Privacy budget exceeded! Spent: %.2f, Limit: %.2f", self.spent_epsilon, self.total_epsilon)
            return False
        self.spent_epsilon += epsilon
        self.spent_delta += delta
        self.rounds += 1
        return True

    @property
    def remaining_epsilon(self) -> float:
        return self.total_epsilon - self.spent_epsilon

    @property
    def budget_fraction_used(self) -> float:
        return self.spent_epsilon / self.total_epsilon if self.total_epsilon > 0 else 1.0
