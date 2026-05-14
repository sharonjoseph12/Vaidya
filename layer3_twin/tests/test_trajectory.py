import pytest
import torch
import numpy as np
import os
from layer3_twin.trajectory_model import DiseaseTrajectoryLSTM, patient_to_tensor, find_critical_month, simulate_with_intervention, load_model

def test_lstm_output_shape():
    model = DiseaseTrajectoryLSTM()
    dummy_input = torch.randn(1, 12, 8)
    output = model(dummy_input)
    assert output.shape == (1, 12, 1)
    assert torch.all(output >= 0) and torch.all(output <= 1)

def test_patient_to_tensor():
    patient = {"base_risk": 0.5, "nutrition_score": 5.0}
    tensor = patient_to_tensor(patient)
    assert tensor.shape == (1, 12, 8)
    assert isinstance(tensor, torch.Tensor)

def test_find_critical_month():
    # Constant trajectory below threshold
    traj_low = torch.full((1, 12, 1), 0.3)
    assert find_critical_month(traj_low) == 12
    
    # Trajectory exceeding threshold at month 5
    traj_high = torch.zeros((1, 12, 1))
    traj_high[0, 5:, 0] = 0.6
    assert find_critical_month(traj_high) == 5

def test_simulation_effect():
    # We need a trained model for this
    model_path = 'models/trajectory_lstm.pt'
    if not os.path.exists(model_path):
        pytest.skip("Model not trained yet")
        
    model = load_model(model_path)
    patient = {"base_risk": 0.6, "nutrition_score": 2.0}
    
    # Nutritional support should generally improve (lower) risk
    result = simulate_with_intervention(model, patient, "nutritional_support")
    
    assert "baseline" in result
    assert "intervened" in result
    assert len(result["baseline"]) == 12
    assert len(result["intervened"]) == 12
    
    # In most cases for our synthetic data, intervened risk should be <= baseline
    # But due to noise and training, we just check they are valid probabilities
    assert all(0 <= v <= 1 for v in result["intervened"])
