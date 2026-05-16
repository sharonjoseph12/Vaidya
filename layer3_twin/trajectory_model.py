import os
import torch
import torch.nn as nn
import numpy as np

# T004: Implement DiseaseTrajectoryLSTM
class DiseaseTrajectoryLSTM(nn.Module):
    def __init__(self, input_dim=8, hidden_dim=64, output_dim=1, n_layers=2):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, n_layers, 
                           batch_first=True, dropout=0.3)
        self.fc = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):  # x: (B, T, input_dim)
        out, _ = self.lstm(x)
        return self.sigmoid(self.fc(out))  # (B, T, 1)

# T005: Generate synthetic trajectory training data
def generate_synthetic_trajectories(n=2000):
    data, labels = [], []
    for _ in range(n):
        # Random patient starting state
        base_risk = np.random.uniform(0.2, 0.9)
        nutrition = np.random.uniform(1, 10)
        # Trajectory: sigmoid progression with noise
        t = np.arange(12)
        risk_curve = base_risk / (1 + np.exp(-0.3*(t - 6*(1-nutrition/10))))
        risk_curve += np.random.normal(0, 0.002, 12)
        risk_curve = np.clip(risk_curve, 0, 1)
        
        # Features: risk_curve, nutrition, noise (x6 to make 8 dims)
        features = np.column_stack([
            risk_curve,
            np.full(12, nutrition),
            np.random.normal(0, 0.1, 12),
            np.random.normal(0, 0.1, 12),
            np.random.normal(0, 0.1, 12),
            np.random.normal(0, 0.1, 12),
            np.random.normal(0, 0.1, 12),
            np.random.normal(0, 0.1, 12)
        ])
        data.append(features)
        labels.append(risk_curve)
    return np.array(data), np.array(labels)

# T006: Patient dict to tensor helper
def patient_to_tensor(patient_features):
    # Patient features is a dict, we need to map it to the 8-dim input
    # Assuming baseline risk is derived from the first value, and nutrition from nutrition_score
    base_risk = patient_features.get("base_risk", 0.5)
    nutrition = patient_features.get("nutrition_score", 5.0)
    
    t = np.arange(12)
    risk_curve = base_risk / (1 + np.exp(-0.3*(t - 6*(1-nutrition/10))))
    
    features = np.column_stack([
        risk_curve,
        np.full(12, nutrition),
        np.zeros(12),
        np.zeros(12),
        np.zeros(12),
        np.zeros(12),
        np.zeros(12),
        np.zeros(12)
    ])
    return torch.FloatTensor(features).unsqueeze(0)  # (1, 12, 8)

# T008 & T009: Training loop and save model
def train_and_save_model(model_path='models/trajectory_lstm.pt'):
    print("Generating synthetic data...")
    X, y = generate_synthetic_trajectories(2000)
    X_tensor = torch.FloatTensor(X)
    y_tensor = torch.FloatTensor(y).unsqueeze(-1)
    
    model = DiseaseTrajectoryLSTM()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    
    print("Training model...")
    for epoch in range(500):
        loss = criterion(model(X_tensor), y_tensor)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        if epoch % 50 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item():.4f}")
    
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    torch.save(model.state_dict(), model_path)
    print(f"Model saved to {model_path}")
    return model

def load_model(model_path='models/trajectory_lstm.pt'):
    model = DiseaseTrajectoryLSTM()
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, weights_only=True))
    else:
        print(f"Model not found at {model_path}. Training new model...")
        model = train_and_save_model(model_path)
    model.eval()
    return model

# T010: Find critical month
def find_critical_month(trajectory, threshold=0.5):
    # trajectory shape: (1, 12, 1) or (12,)
    traj = trajectory.squeeze().detach().numpy()
    critical_months = np.where(traj > threshold)[0]
    if len(critical_months) > 0:
        return critical_months[0]
    return 12  # Doesn't exceed threshold within 12 months

# T012: Intervention effects mapping
INTERVENTION_EFFECTS = {
    "nutritional_support": {"nutrition_score": +4, "bmi": +2},
    "dots_treatment":      {"disease_progression": -0.6},
    "lifestyle_change":    {"activity_level": +3, "smoking": -1},
    "referral_phc":        {"treatment_access": +1},
    "iron_supplement":     {"hemoglobin": +2},
    "emergency_108":       {"treatment_access": +5}
}

# T011: Simulate with intervention
def simulate_with_intervention(model, patient_features, intervention):
    modified = patient_features.copy()
    if intervention in INTERVENTION_EFFECTS:
        for feat, delta in INTERVENTION_EFFECTS[intervention].items():
            modified[feat] = modified.get(feat, 0) + delta
            
            # Clinical bounds
            if feat == "nutrition_score":
                modified[feat] = min(max(modified[feat], 1), 10)
            elif feat == "bmi":
                modified[feat] = min(max(modified[feat], 13), 40)
            elif feat == "smoking":
                modified[feat] = min(max(modified[feat], 0), 1)
            elif feat == "hemoglobin":
                modified[feat] = min(max(modified[feat], 6), 16)
    
    baseline_traj = model(patient_to_tensor(patient_features))
    intervened_traj = model(patient_to_tensor(modified))
    
    months_saved = (
        find_critical_month(baseline_traj) - 
        find_critical_month(intervened_traj)
    )
    
    return {
        "baseline": baseline_traj.squeeze().tolist(),
        "intervened": intervened_traj.squeeze().tolist(),
        "months_progression_delayed": max(0, int(months_saved)),
        "intervention": intervention
    }

# T015: Smoke test
if __name__ == "__main__":
    print("Testing LSTM model training and simulation...")
    model = load_model()
    
    patient = {
        "base_risk": 0.4,
        "nutrition_score": 3.0,
        "bmi": 17.0,
        "smoking": 1
    }
    
    print(f"Initial patient state: {patient}")
    result = simulate_with_intervention(model, patient, "nutritional_support")
    
    print(f"Intervention applied: nutritional_support")
    print(f"Baseline critical month: {find_critical_month(model(patient_to_tensor(patient)))}")
    print(f"Months delayed: {result['months_progression_delayed']}")
    print("Baseline trajectory:", [f"{v:.3f}" for v in result['baseline']])
    print("Intervened trajectory:", [f"{v:.3f}" for v in result['intervened']])
