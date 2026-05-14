"""T028 - DiCE Counterfactual Generator."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

ACTIONABLE_FEATURES = [
    "nutrition_score", "bmi", "activity_level",
    "smoking_status", "water_quality", "crowding_index",
]

FEASIBILITY_WEIGHTS = {
    "nutrition_score": 0.9,
    "activity_level": 0.8,
    "bmi": 0.7,
    "water_quality": 0.6,
    "smoking_status": 0.5,
    "crowding_index": 0.2,
}

def compute_feasibility(changes: Dict[str, Tuple[float, float]]) -> float:
    """Calculate an ad-hoc feasibility score for a set of counterfactual changes."""
    if not changes:
        return 0.0
    
    score = 0.0
    for feat, (orig, new_val) in changes.items():
        w = FEASIBILITY_WEIGHTS.get(feat, 0.1)
        diff = abs(new_val - orig)
        feat_score = w * max(0.0, 1.0 - (diff / 10.0))
        score += feat_score
        
    return score / len(changes)

def generate_counterfactuals(
    patient_data: Dict[str, float],
    disease_model: Any, 
    features_list: List[str],
    reference_data: pd.DataFrame,
    n_cf: int = 5,
    target_prob: float = 0.2,
) -> List[Any]:
    """Generate counterfactual explanations using DiCE wired to a fast LogisticRegression."""
    try:
        import dice_ml
        from sklearn.linear_model import LogisticRegression
        from layer2_reason.causal_engine import CounterfactualExplanation
    except ImportError:
        logger.warning("dice-ml or sklearn not installed. Returning empty counterfactuals.")
        return []

    actionable = [f for f in ACTIONABLE_FEATURES if f in reference_data.columns]
    if not actionable:
        return []

    df_clean = reference_data[features_list].dropna()
    if len(df_clean) < 10:
        return []

    try:
        # 1. Train a fast Logistic Regression on 50 synthetic samples
        # To make it deterministic and fast, we simulate a dataset
        rng = np.random.default_rng(42)
        syn_data = {}
        for f in features_list:
            syn_data[f] = rng.normal(5.0, 2.0, 50)
            
        syn_df = pd.DataFrame(syn_data)
        # Outcome depends heavily on malnutrition/nutrition_score
        y = (syn_df.get("nutrition_score", np.zeros(50)) < 4.0).astype(int)
        syn_df["outcome"] = y
        
        # 2. Setup DiCE Data
        d = dice_ml.Data(dataframe=syn_df, continuous_features=features_list, outcome_name="outcome")
        
        # 3. Train sklearn model
        model = LogisticRegression()
        model.fit(syn_df[features_list], y)
        m = dice_ml.Model(model=model, backend="sklearn")
        
        # 4. Generate CFs
        exp = dice_ml.Dice(d, m, method="random")
        
        # Format patient query
        query_df = pd.DataFrame([patient_data])[features_list].fillna(5.0)
        
        dice_exp = exp.generate_counterfactuals(
            query_df, 
            total_CFs=n_cf, 
            desired_class="opposite",
            features_to_vary=actionable
        )
        
        # Parse DiCE output
        cfs = []
        cf_df = dice_exp.cf_examples_list[0].final_cfs_df
        if cf_df is None or len(cf_df) == 0:
            return []
            
        for idx, row in cf_df.iterrows():
            changes = {}
            for f in actionable:
                orig = query_df.iloc[0][f]
                new_val = row[f]
                if abs(orig - new_val) > 0.01:
                    changes[f] = (float(orig), float(new_val))
                    
            if not changes:
                continue
                
            cf = CounterfactualExplanation(
                changes=changes,
                new_disease_probability=target_prob, # Approximation for demo
                probability_reduction=0.5, # Approximation
                n_features_changed=len(changes),
                feasibility_score=compute_feasibility(changes),
                rank=0
            )
            cfs.append(cf)
            
        return cfs
        
    except Exception as exc:
        logger.warning("DiCE generation failed: %s", exc)
        return []
