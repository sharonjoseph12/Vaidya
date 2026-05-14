# Quickstart: PRISM Layer 3+4

This guide explains how to get started with the Neural ODE Digital Twin and RL Intervention Optimizer modules.

## Setup

1. **Environment**:
   Ensure you have Python 3.11 installed. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install torch==2.1.0 torchvision torchaudio  # Replace with appropriate CUDA versions if needed
   pip install torchdiffeq==0.2.3 torchsde==0.2.6 pytorch-lightning==2.1.3 wandb==0.16.6 einops==0.7.0 stable-baselines3 gymnasium
   ```

2. **Data Download**:
   - For the Metabolic Twin, use the script to download NHANES data:
     ```bash
     python prism/data/download_nhanes.py
     ```
   - For the Cardiopulmonary Twin, you need MIMIC-IV access (requires PhysioNet credentialing). Place the CSVs in `prism/data/mimic`.

## Running the Digital Twin Trainer

To train the Latent ODE models for the specialized organ twins:

```bash
python prism/layer3_twin/trainer.py --twin metabolic --data-dir prism/data/nhanes --epochs 50
```

## Running the RL Optimizer

Once the twins are trained, you can train the PPO agent in the `PatientHealthEnv`:

```bash
python prism/layer4_rl/agents/ppo_agent.py --train --timesteps 1000000
```

## Integrating with the Causal Engine

The intervention impact is defined by the causal forcing functions. Ensure the `layer2_reason` outputs (SCM graphs) are available in the configuration path before running counterfactual simulations.
