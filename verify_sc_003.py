import torch
import numpy as np
from layer3_twin.trajectory_model import DiseaseTrajectoryLSTM, generate_synthetic_trajectories, load_model

def verify_sc_003():
    print("Verifying SC-003: LSTM trajectory MAE < 0.4%...")
    model = load_model()
    
    # Generate test set
    n_test = 500
    X_test, y_test = generate_synthetic_trajectories(n_test)
    X_tensor = torch.FloatTensor(X_test)
    
    model.eval()
    with torch.no_grad():
        preds = model(X_tensor).squeeze().numpy()
    
    mae = np.mean(np.abs(preds - y_test))
    print(f"Calculated MAE: {mae:.6f}")
    
    if mae < 0.004:  # 0.4%
        print("SC-003: PASS")
    else:
        print("SC-003: FAIL")

if __name__ == "__main__":
    verify_sc_003()
