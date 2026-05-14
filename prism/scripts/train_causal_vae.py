"""T046 - Training script for CausalVAE."""
import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import torch
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
except ImportError:
    torch = None

from layer2_reason.counterfactuals.causal_vae import CausalVAE, causal_vae_loss

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", default="data/processed/panel_dataset.pkl")
    parser.add_argument("--latent-dim", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--beta", type=float, default=4.0)
    parser.add_argument("--output", default="layer2_reason/vae_weights/causal_vae.pt")
    parser.add_argument("--max-patients", type=int, default=500)
    args = parser.parse_args()

    if not torch:
        logger.error("PyTorch required for training.")
        return

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Dummy data for tests (if panel not found)
    panel_path = Path(args.panel)
    if panel_path.exists():
        df = pd.read_pickle(panel_path)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        data = df[numeric_cols].fillna(0.0).values
        if len(data) > args.max_patients:
            data = data[:args.max_patients]
    else:
        logger.warning("Panel not found, using synthetic data")
        data = np.random.randn(args.max_patients, 15).astype(np.float32)

    x_tensor = torch.tensor(data, dtype=torch.float32)
    dataset = TensorDataset(x_tensor)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)

    input_dim = x_tensor.shape[1]
    model = CausalVAE(input_dim=input_dim, latent_dim=args.latent_dim)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)

    logger.info("Starting training for %d epochs...", args.epochs)
    
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0
        
        for batch in loader:
            x_batch = batch[0]
            optimizer.zero_grad()
            
            x_recon, mu, logvar, _ = model(x_batch)
            loss, metrics = causal_vae_loss(
                x_recon, x_batch, mu, logvar, model.causal_mask, beta=args.beta
            )
            
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        logger.info("Epoch %d | Loss: %.4f | h(A): %.4f", epoch+1, total_loss / len(loader), metrics["h_A"])

    torch.save(model.state_dict(), out_path)
    logger.info("Saved weights to %s", out_path)


if __name__ == "__main__":
    main()
