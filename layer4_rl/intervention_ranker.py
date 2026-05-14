# PRISM Layer 4: Intervention Optimizer
# ========================================
# Rule-based intervention ranking based on cost-effectiveness, 
# feasibility, and clinical impact (QALY).

INTERVENTION_DB = {
    "nutritional_support": {"cost": 0, "feasibility": 0.9, "qaly": 0.8},
    "dots_treatment":      {"cost": 0, "feasibility": 0.7, "qaly": 2.1},
    "lifestyle_change":    {"cost": 0, "feasibility": 0.6, "qaly": 0.5},
    "iron_supplement":     {"cost": 120, "feasibility": 0.95, "qaly": 0.7},
    "refer_specialist":    {"cost": 200, "feasibility": 0.5, "qaly": 1.2},
    "emergency_108":       {"cost": 0, "feasibility": 1.0, "qaly": 3.0}
}

def rank_interventions(disease_prob, patient_income=8000):
    """
    Score and rank interventions based on a cost-effectiveness formula.
    Score = (QALY * disease_prob * feasibility) / max(cost/income, 0.01)
    """
    ranked = []
    for name, info in INTERVENTION_DB.items():
        # Avoid division by zero, use a small epsilon
        cost_factor = max(info['cost'] / max(patient_income, 1), 0.01)
        score = (info['qaly'] * disease_prob * info['feasibility']) / cost_factor
        
        ranked.append({
            "name": name,
            "score": score,
            "cost": info['cost'],
            "free": info['cost'] == 0,
            "feasibility": info['feasibility'],
            "qaly": info['qaly']
        })
    
    # Sort by score descending and take top 3
    return sorted(ranked, key=lambda x: x['score'], reverse=True)[:3]

if __name__ == "__main__":
    print("Testing Intervention Ranker...")
    disease_prob = 0.65
    income = 8000
    top3 = rank_interventions(disease_prob, income)
    
    print(f"Top 3 interventions for disease_prob={disease_prob}, income={income}:")
    for i, intervention in enumerate(top3):
        print(f"{i+1}. {intervention['name']} (Score: {intervention['score']:.2f}, Free: {intervention['free']})")
