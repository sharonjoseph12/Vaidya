import argparse
import os
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.logger import configure
from layer4_rl.env.patient_env import PatientHealthEnv

def train_ppo(args):
    # Mock digital twin for the environment
    class MockTwin:
        pass
    
    twin_model = MockTwin()
    env = PatientHealthEnv(twin_model, max_steps=args.max_steps)
    
    # Configure logger
    tmp_path = "prism/layer4_rl/logs/"
    os.makedirs(tmp_path, exist_ok=True)
    new_logger = configure(tmp_path, ["stdout", "csv", "tensorboard"])
    
    # Initialize PPO Agent
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1,
        learning_rate=args.lr,
        n_steps=args.n_steps,
        batch_size=args.batch_size
    )
    
    model.set_logger(new_logger)
    
    # Save a checkpoint every 10000 steps
    checkpoint_callback = CheckpointCallback(
        save_freq=args.save_freq,
        save_path="prism/layer4_rl/models/",
        name_prefix="ppo_patient_twin"
    )
    
    print(f"Starting PPO training for {args.timesteps} timesteps...")
    model.learn(total_timesteps=args.timesteps, callback=checkpoint_callback)
    
    # Save final model
    model.save("prism/layer4_rl/models/ppo_patient_twin_final")
    print("Training complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=100000)
    parser.add_argument("--max-steps", type=int, default=30)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--n-steps", type=int, default=2048)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--save-freq", type=int, default=10000)
    
    args = parser.parse_args()
    train_ppo(args)
