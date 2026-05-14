"""
Reward logic for the RL Intervention Optimizer.
Combines Quality-Adjusted Life Years (QALY) and Ayushman Bharat costs.
"""

def calculate_qaly(patient_state, predicted_trajectory):
    """
    Calculate the expected QALY based on the predicted health trajectory.
    Dummy implementation: assumes higher biomarker values are 'worse' health.
    """
    # Average the biomarker values over time to represent health degradation
    avg_biomarkers = sum([sum(t) for t in predicted_trajectory]) / (len(predicted_trajectory) * len(predicted_trajectory[0]))
    
    # QALY is bounded between 0 (death) and 1 (perfect health)
    qaly = max(0.0, 1.0 - (avg_biomarkers / 100.0))
    return qaly

def get_intervention_cost(action_id):
    """
    Get the Ayushman Bharat cost for a specific intervention.
    """
    # Dummy cost table (in INR)
    cost_table = {
        0: 0,       # No action
        1: 50,      # Basic lab test
        2: 200,     # Advanced diagnostic
        3: 500,     # Outpatient medication
        4: 2000,    # Inpatient monitoring
        # ... other actions up to 14
    }
    return cost_table.get(action_id, 100)

def calculate_reward(patient_state, action_id, predicted_trajectory):
    """
    Calculate the total RL reward: QALY gain - normalized cost.
    """
    qaly = calculate_qaly(patient_state, predicted_trajectory)
    cost = get_intervention_cost(action_id)
    
    # Normalize cost to be comparable to QALY (e.g., 1 QALY = 1,000,000 INR)
    normalized_cost = cost / 1000000.0
    
    # Reward is QALY minus cost penalty
    reward = qaly - normalized_cost
    return reward
