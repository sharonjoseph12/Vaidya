import gymnasium
import numpy as np
import random
from .cost_database import INTERVENTIONS

class PatientHealthEnv(gymnasium.Env):
  """
  MDP environment for patient health management.
  State: patient health features + trajectory + causal weights
  Action: intervention selection
  Reward: QALY gain - cost - side effects
  """
  def __init__(self, patient_cohort, digital_twin, episode_length_months=12):
    super().__init__()
    
    self.intervention_keys = list(INTERVENTIONS.keys())
    N_ACTIONS = len(self.intervention_keys)
    N_STATE_FEATURES = 30  # biomarkers + trajectory features + demographics
    
    self.action_space = gymnasium.spaces.Discrete(N_ACTIONS)
    self.observation_space = gymnasium.spaces.Box(
        low=-np.inf, high=np.inf, 
        shape=(N_STATE_FEATURES,), dtype=np.float32
    )
    
    self.patient_cohort = patient_cohort
    self.twin = digital_twin
    self.episode_length = episode_length_months * 30  # days
  
  def reset(self, seed=None, options=None):
    super().reset(seed=seed)
    # Sample random patient from cohort
    self.current_patient = random.choice(self.patient_cohort)
    self.current_day = 0
    self.applied_interventions = []
    self.patient_state = self._get_initial_state()
    return self._get_observation(), {}
  
  def _get_initial_state(self):
      # Dummy implementation: start with initial biomarkers
      return np.zeros(30, dtype=np.float32)

  def _get_observation(self):
      return self.patient_state

  def step(self, action):
    intervention_key = self.intervention_keys[action]
    
    # Apply intervention to digital twin
    # In a real setup, this would call the Neural ODE twin
    new_state = self.twin.intervene(
        self.patient_state, intervention_key, self.current_day)
    
    # Compute reward
    reward = self._compute_reward(
        self.patient_state, new_state, intervention_key)
    
    self.patient_state = new_state
    self.current_day += 30  # monthly decisions
    self.applied_interventions.append(intervention_key)
    
    done = self.current_day >= self.episode_length
    truncated = False
    
    return self._get_observation(), reward, done, truncated, {}
  
  def _compute_reward(self, old_state, new_state, intervention):
    # QALY improvement (Placeholder logic)
    qaly_gain = self._compute_qaly_gain(old_state, new_state) * 365
    
    # Cost (normalized by monthly income bracket)
    income = self.current_patient.get('monthly_income', 8000)
    cost_normalized = INTERVENTIONS[intervention]['cost_private'] / income
    
    # Side effect penalty
    side_effect_penalty = INTERVENTIONS[intervention]['side_effects'] * 10
    
    # Unnecessary intervention penalty (discourage over-treatment)
    redundancy_penalty = 0.1 if intervention in self.applied_interventions else 0
    
    return qaly_gain - cost_normalized - side_effect_penalty - redundancy_penalty

  def _compute_qaly_gain(self, old_state, new_state):
      # Simplified QALY logic
      return 0.1 # Example gain
