"""
API for the RL Intervention Optimizer service.
"""
from typing import List, Dict

class InterventionOptimizerService:
    def __init__(self, ppo_agent, twin_service):
        self.agent = ppo_agent
        self.twin_service = twin_service

    def recommend_intervention(self, patient_state) -> Dict:
        """
        Recommend the optimal intervention sequence for a given patient state.
        """
        # Convert patient_state to numpy array if needed
        # In this stub, we assume it's already an array compatible with the gym env observation space
        
        # Query the PPO policy for the best action
        # deterministic=True ensures we get the argmax action, not a sampled one
        action, _states = self.agent.predict(patient_state, deterministic=True)
        
        # Map the action ID back to a readable string based on our cost table mapping
        intervention_names = {
            0: "No action",
            1: "Basic lab test",
            2: "Advanced diagnostic",
            3: "Outpatient medication",
            4: "Inpatient monitoring"
        }
        
        recommended_action_str = intervention_names.get(int(action), f"Unknown Action ID: {action}")
        
        return {
            "patient_id": getattr(patient_state, 'patient_id', "unknown"),
            "recommended_action_id": int(action),
            "recommended_action_name": recommended_action_str,
            "rationale": "Recommended by PPO policy trained on QALY and Ayushman Bharat cost optimization."
        }
