"""
Export PyTorch Latent ODE models to ONNX and TFLite for edge deployment.
"""
import torch
import os
import argparse
from layer3_twin.organ_twins.metabolic_twin import MetabolicTwin

def export_to_onnx(model, save_path):
    # Dummy inputs for tracing
    # (batch_size, seq_len, input_dim)
    dummy_obs = torch.randn(1, 10, model.model.encoder.rnn_cell.input_size)
    dummy_obs_times = torch.linspace(0, 10, steps=10)
    dummy_target_times = torch.linspace(0, 30, steps=30)
    
    print(f"Exporting model to ONNX at {save_path}...")
    try:
        torch.onnx.export(
            model,
            (dummy_obs, dummy_obs_times, dummy_target_times),
            save_path,
            export_params=True,
            opset_version=14,
            do_constant_folding=True,
            input_names=['observations', 'obs_times', 'target_times'],
            output_names=['pred_x', 'mean', 'logvar']
        )
        print("Export successful.")
    except Exception as e:
        print(f"Error during ONNX export: {e}")
        print("Note: Latent ODEs with dynamic solvers often require custom ONNX ops or static horizons.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="metabolic")
    parser.add_argument("--output", type=str, default="prism/models/metabolic_twin.onnx")
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    if args.model == "metabolic":
        model = MetabolicTwin()
        # In reality, we'd load weights here: model.load_state_dict(torch.load('path'))
        model.eval()
        export_to_onnx(model, args.output)
