"""
Weights & Biases logging configuration.
"""
import wandb
import os

def init_wandb(project_name="prism-digital-twin", run_name=None, config=None):
    """
    Initialize a W&B run.
    """
    # Check if W&B API key is available
    if "WANDB_API_KEY" not in os.environ:
        print("WARNING: WANDB_API_KEY not found in environment. W&B logging will be disabled or run offline.")
        os.environ["WANDB_MODE"] = "offline"
    
    run = wandb.init(
        project=project_name,
        name=run_name,
        config=config,
        reinit=True
    )
    return run
