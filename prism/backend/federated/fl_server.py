"""
PRISM Platform — Federated Learning Server
Custom FedAvg strategy with differential privacy and quality filtering.
"""
import logging
import numpy as np

logger = logging.getLogger(__name__)

try:
    import flwr as fl
    from flwr.server.strategy import FedAvg
    FLWR_AVAILABLE = True
except ImportError:
    FLWR_AVAILABLE = False
    logger.warning("Flower (flwr) not installed — FL features disabled")


if FLWR_AVAILABLE:
    class PRISMFederatedStrategy(FedAvg):
        """FedAvg with differential privacy noise and client quality filtering."""

        def __init__(self, dp_epsilon=1.0, dp_delta=1e-5, min_clients=2, **kwargs):
            super().__init__(
                min_fit_clients=min_clients,
                min_evaluate_clients=min_clients,
                min_available_clients=min_clients,
                **kwargs,
            )
            self.dp_epsilon = dp_epsilon
            self.dp_delta = dp_delta
            self.round_metrics = []

        def aggregate_fit(self, server_round, results, failures):
            if not results:
                return None
            # Filter: reject clients with loss > 3× median
            losses = [r.metrics.get("train_loss", 0) for _, r in results]
            median_loss = np.median(losses) if losses else 0
            filtered = [(c, r) for c, r in results if r.metrics.get("train_loss", 0) <= 3 * median_loss]

            aggregated = super().aggregate_fit(server_round, filtered, failures)
            if aggregated:
                weights, metrics = aggregated
                noisy_weights = self._add_dp_noise(weights)
                self.round_metrics.append({
                    "round": server_round,
                    "n_clients": len(filtered),
                    "n_rejected": len(results) - len(filtered),
                })
                return noisy_weights, metrics
            return aggregated

        def _add_dp_noise(self, weights):
            sensitivity = 2.0
            noise_std = sensitivity * np.sqrt(2 * np.log(1.25 / self.dp_delta)) / self.dp_epsilon
            return [np.array(w) + np.random.normal(0, noise_std, np.array(w).shape) for w in weights]


def start_fl_server(port=8080, num_rounds=100):
    """Start the Flower FL server."""
    if not FLWR_AVAILABLE:
        logger.error("Cannot start FL server: flwr not installed")
        return
    strategy = PRISMFederatedStrategy(dp_epsilon=1.0, dp_delta=1e-5, min_clients=2)
    fl.server.start_server(
        server_address=f"0.0.0.0:{port}",
        config=fl.server.ServerConfig(num_rounds=num_rounds),
        strategy=strategy,
    )


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--rounds", type=int, default=100)
    args = parser.parse_args()
    start_fl_server(args.port, args.rounds)
