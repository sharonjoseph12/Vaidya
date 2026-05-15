import os
import random

MODEL_DIR = os.path.dirname(__file__)

class MockModel:
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def infer(self, data):
        # Deterministic random based on data hash or length
        seed = len(str(data)) if data else 42
        random.seed(seed)
        
        if self.name == "YAMNet":
            # Simulate audio classification
            return {
                "TB_Cough": random.uniform(0.6, 0.9),
                "Wheezing": random.uniform(0.1, 0.4),
                "Normal": random.uniform(0.01, 0.1)
            }
        elif self.name == "LSTM":
            # Simulate trajectory
            base_prob = random.uniform(0.6, 0.85)
            return {
                "months_to_critical": round(random.uniform(3.0, 7.0), 1),
                "months_to_critical_with_intervention": round(random.uniform(15.0, 24.0), 1),
                "intervention_applied": "Nutritional_Supplementation",
                "without_intervention": [
                    {"month": 0, "values": {"tb_prob": base_prob}},
                    {"month": 3, "values": {"tb_prob": min(1.0, base_prob + 0.08)}},
                    {"month": 6, "values": {"tb_prob": min(1.0, base_prob + 0.15)}}
                ],
                "with_best_intervention": [
                    {"month": 0, "values": {"tb_prob": base_prob}},
                    {"month": 3, "values": {"tb_prob": max(0.0, base_prob - 0.15)}},
                    {"month": 6, "values": {"tb_prob": max(0.0, base_prob - 0.35)}}
                ]
            }
        elif self.name == "CausalExplainer":
            # Simulate causal attribution
            return {
                "attributions": {"malnutrition": 0.38, "poor_ventilation": 0.24, "prior_infection": 0.21, "genetic_factors": 0.17},
                "narrative": "Based on causal inference, the high risk is predominantly driven by malnutrition and poor ventilation.",
                "counterfactuals": [{
                    "changes": {"malnutrition": ["Severe", "Normal"]},
                    "original_probability": 0.79,
                    "new_probability": 0.31,
                    "feasibility_score": 0.85
                }]
            }
        elif self.name == "RLOptimizer":
            # Simulate RL output
            return {
                "recommendations": [
                    {
                        "rank": 1,
                        "intervention": "Nutritional_Supplementation_and_DOTS",
                        "description": "Provide caloric support and initiate DOTS therapy.",
                        "cost_private": 400,
                        "cost_govt": 0,
                        "qaly_gain": round(random.uniform(2.0, 3.5), 1),
                        "time_to_effect_days": 30,
                        "side_effect_risk": 0.05,
                        "scheme": "Nikshay Poshan Yojana",
                        "nearest_facility": {"name": "Primary Health Center", "distance_km": 1.2}
                    }
                ],
                "pareto_options": [
                    {"cost": 0, "qaly_gain": 2.0, "label": "Free Government Treatment"},
                    {"cost": 1400, "qaly_gain": 3.0, "label": "Private Specialist"},
                    {"cost": 300, "qaly_gain": 2.5, "label": "NGO Supported Program"}
                ]
            }

def load_yamnet_model():
    model_path = os.path.join(MODEL_DIR, "prism_yamnet_audio.h5")
    return MockModel("YAMNet", model_path)

def load_trajectory_model():
    model_path = os.path.join(MODEL_DIR, "lstm_trajectory.pth")
    return MockModel("LSTM", model_path)

def load_causal_explainer():
    model_path = os.path.join(MODEL_DIR, "causal_explainer.pkl")
    return MockModel("CausalExplainer", model_path)

def load_rl_optimizer():
    # RL agent might be an API or another artifact
    return MockModel("RLOptimizer", "mock_rl_agent")
