"""
PRISM Platform — Federated Learning Hospital Client
Trains on local hospital data, clips gradients, sends only weight updates.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

try:
    import flwr as fl
    FLWR_AVAILABLE = True
except ImportError:
    FLWR_AVAILABLE = False


if FLWR_AVAILABLE:
    class PRISMHospitalClient(fl.client.NumPyClient):
        """FL client that trains on local hospital data. Raw data never leaves."""

        def __init__(self, model, local_data_path: str, hospital_id: str):
            self.model = model
            self.local_data_path = local_data_path
            self.hospital_id = hospital_id
            self.max_grad_norm = 1.0

        def get_parameters(self, config):
            return [p.detach().cpu().numpy() for p in self.model.parameters()]

        def set_parameters(self, parameters):
            import torch
            for param, new_val in zip(self.model.parameters(), parameters):
                param.data = torch.tensor(new_val, dtype=param.dtype)

        def fit(self, parameters, config):
            self.set_parameters(parameters)
            # Train locally
            train_loss = self._train_local(
                epochs=config.get("local_epochs", 3),
                lr=config.get("lr", 1e-4),
            )
            # Clip gradient updates
            new_params = self.get_parameters(config)
            clipped = self._clip_updates(parameters, new_params)
            n_samples = self._count_samples()
            return clipped, n_samples, {"train_loss": train_loss}

        def evaluate(self, parameters, config):
            self.set_parameters(parameters)
            loss, accuracy = self._evaluate_local()
            return loss, self._count_samples(), {"accuracy": accuracy}

        def _train_local(self, epochs, lr):
            logger.info("Training locally at %s for %d epochs", self.hospital_id, epochs)
            return 0.5  # Mock loss

        def _evaluate_local(self):
            return 0.3, 0.85  # Mock loss, accuracy

        def _count_samples(self):
            return 100  # Mock

        def _clip_updates(self, old_params, new_params):
            updates = [np.array(n) - np.array(o) for o, n in zip(old_params, new_params)]
            total_norm = np.sqrt(sum(np.sum(u**2) for u in updates))
            if total_norm > self.max_grad_norm:
                scale = self.max_grad_norm / total_norm
                updates = [u * scale for u in updates]
            return [np.array(o) + u for o, u in zip(old_params, updates)]
