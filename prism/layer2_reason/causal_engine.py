import dowhy
from dowhy import CausalModel
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Generate synthetic cohort once at startup
np.random.seed(42)
n = 2000
df = pd.DataFrame({
    'malnutrition':      np.random.beta(2,5,n),
    'crowding_index':    np.random.exponential(2,n).clip(1,8),
    'bmi':               np.random.normal(20,4,n).clip(13,40),
    'smoking':           np.random.binomial(1,0.25,n).astype(float),
    'nutrition_score':   np.random.uniform(1,10,n),
    'hemoglobin':        np.random.normal(10,2,n).clip(6,16),
    'ventilation_score': np.random.uniform(1,10,n),
    'age':               np.random.randint(18,75,n).astype(float),
})
df['TB'] = ((df['malnutrition']>0.5).astype(int) +
            (df['crowding_index']>3).astype(int) +
            (df['bmi']<18).astype(int) > 1).astype(int)
df['Anemia'] = (df['hemoglobin'] < 10).astype(int)
df['COPD'] = df['smoking'] * (df['age'] > 40).astype(int)

CAUSAL_GRAPH = """digraph {
    malnutrition -> TB;
    malnutrition -> Anemia;
    malnutrition -> hemoglobin;
    crowding_index -> TB;
    bmi -> TB;
    bmi -> Anemia;
    smoking -> COPD;
    smoking -> TB;
    ventilation_score -> TB;
    nutrition_score -> malnutrition;
    nutrition_score -> hemoglobin;
}"""

# Pre-build DoWhy models for each treatment-outcome pair
TREATMENT_OUTCOME_PAIRS = {
    'TB': ['malnutrition', 'crowding_index', 'nutrition_score', 'smoking'],
    'Anemia': ['malnutrition', 'nutrition_score', 'hemoglobin'],
    'COPD': ['smoking']
}

dowhy_models = {}
for disease, treatments in TREATMENT_OUTCOME_PAIRS.items():
    dowhy_models[disease] = {}
    for treatment in treatments:
        try:
            m = CausalModel(
                data=df,
                treatment=treatment,
                outcome=disease,
                graph=CAUSAL_GRAPH
            )
            estimand = m.identify_effect(proceed_when_unidentifiable=True)
            estimate = m.estimate_effect(
                estimand,
                method_name="backdoor.linear_regression",
                target_units="ate"
            )
            dowhy_models[disease][treatment] = {
                'model': m,
                'estimand': estimand, 
                'ate': estimate.value  # Average Treatment Effect
            }
        except Exception as e:
            logger.warning(f"Skipping {treatment}->{disease}: {e}")

def get_causal_attribution(disease: str, patient_features: dict) -> dict:
    """
    Real causal attribution using DoWhy ATEs.
    ATE × patient's feature value = that factor's contribution.
    """
    if disease not in dowhy_models:
        return {}
    
    attributions = {}
    for treatment, info in dowhy_models[disease].items():
        patient_val = patient_features.get(treatment, 0)
        # Contribution = ATE × how much this patient has of this factor
        contribution = abs(info['ate']) * float(patient_val)
        attributions[treatment] = contribution
    
    # Normalize
    total = sum(attributions.values()) or 1
    return {k: round(v/total, 3) for k,v in 
            sorted(attributions.items(), key=lambda x: x[1], reverse=True)}

def estimate_intervention_effect(
    disease: str, 
    treatment: str, 
    patient_prob: float
) -> float:
    """
    Returns new disease probability after do(treatment=0).
    Uses real DoWhy ATE.
    """
    if disease not in dowhy_models or treatment not in dowhy_models[disease]:
        return patient_prob
    
    ate = dowhy_models[disease][treatment]['ate']
    # ATE = E[Y|do(T=1)] - E[Y|do(T=0)]
    # Intervening (setting T=0) reduces outcome by ATE
    new_prob = max(0, min(1, patient_prob - abs(ate)))
    return round(new_prob, 3)

def full_causal_report(disease_probs: dict, patient_features: dict) -> dict:
    if not disease_probs:
        return {}
        
    top_disease = max(disease_probs, key=disease_probs.get)
    top_prob = disease_probs[top_disease]
    
    attributions = get_causal_attribution(top_disease, patient_features)
    top_cause = next(iter(attributions), None)
    
    interventions = []
    for treatment in (TREATMENT_OUTCOME_PAIRS.get(top_disease, [])):
        new_prob = estimate_intervention_effect(top_disease, treatment, top_prob)
        interventions.append({
            'treatment': treatment,
            'baseline_prob': top_prob,
            'intervened_prob': new_prob,
            'reduction_pct': round((top_prob - new_prob)/max(top_prob, 0.001)*100, 1)
        })
    interventions.sort(key=lambda x: x['reduction_pct'], reverse=True)
    
    narrative = ""
    if interventions and top_cause:
        narrative = (
            f"{top_disease} probability {top_prob:.0%}. "
            f"Primary driver: {top_cause} ({attributions.get(top_cause,0):.0%}). "
            f"Eliminating it reduces probability to "
            f"{interventions[0]['intervened_prob']:.0%}."
        )
    
    return {
        'disease': top_disease,
        'probability': top_prob,
        'attributions': attributions,
        'interventions': interventions,
        'best_intervention': interventions[0] if interventions else None,
        'narrative': narrative,
        'causal_graph_dot': CAUSAL_GRAPH
    }
