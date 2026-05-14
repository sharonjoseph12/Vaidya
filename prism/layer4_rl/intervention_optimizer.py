import numpy as np
from typing import List, Dict
from .cost_database import INTERVENTIONS
from stable_baselines3 import PPO

class InterventionRecommendation:
    def __init__(self, intervention, description, projected_reduction, cost_govt, cost_private, qaly_gain, time_to_effect):
        self.intervention = intervention
        self.description = description
        self.projected_reduction = projected_reduction
        self.cost_govt = cost_govt
        self.cost_private = cost_private
        self.qaly_gain = qaly_gain
        self.time_to_effect = time_to_effect

class PRISMInterventionOptimizer:
  def __init__(self, ppo_model_path, twin_service):
    try:
        self.ppo = PPO.load(ppo_model_path)
    except:
        self.ppo = None # Fallback for demo
    self.twins = twin_service
  
  def optimize(self, patient_state, n_recommendations=3):
    # Get RL policy recommendation
    if self.ppo:
        action, _ = self.ppo.predict(patient_state, deterministic=True)
        top_actions = [action] # Simple version for now
    else:
        # Fallback: rank by QALY weight
        sorted_interventions = sorted(INTERVENTIONS.items(), key=lambda x: x[1]['qaly_weight'], reverse=True)
        top_actions = [name for name, _ in sorted_interventions[:n_recommendations]]
    
    recommendations = []
    for intervention_key in top_actions:
      data = INTERVENTIONS.get(intervention_key, {})
      
      # Simulate effect via digital twin (In real: call self.twins.intervene)
      projected_reduction = data.get('qaly_weight', 0.1) * 0.5 
      
      recommendations.append({
          "intervention": intervention_key,
          "description": data,
          "projected_reduction": projected_reduction,
          "cost_govt": data.get('cost_govt', 0),
          "cost_private": data.get('cost_private', 0),
          "qaly_gain": data.get('qaly_weight', 0),
          "time_to_effect": data.get('time_to_effect_days', 0),
          "evidence_level": "B"
      })
    
    return {
        "recommendations": recommendations,
        "primary_recommendation": recommendations[0] if recommendations else None,
        "narrative": self.build_narrative(recommendations[0]) if recommendations else ""
    }
  
  def build_narrative(self, rec) -> str:
    name = rec['intervention'].replace('_', ' ').title()
    reduction = rec['projected_reduction'] * 100
    return f"Recommended intervention: {name}. Projected risk reduction: {reduction:.1f}%. Cost: ₹{rec['cost_private']} (Private) / Free (Govt)."
