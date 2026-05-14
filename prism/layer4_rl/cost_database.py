# PRISM — Cost Database for RL Optimizer
# Ayushman Bharat (PM-JAY) and Private Market Costs in INR

INTERVENTIONS = {
    "nutritional_support": {
        "cost_govt": 0,          # ICDS scheme
        "cost_private": 800,     # ₹/month
        "side_effects": 0.01,
        "time_to_effect_days": 30,
        "qaly_weight": 0.15
    },
    "refer_phc": {
        "cost_govt": 0,
        "cost_private": 200,
        "side_effects": 0.0,
        "time_to_effect_days": 1,
        "qaly_weight": 0.05
    },
    "dots_tb_treatment": {
        "cost_govt": 0,          # RNTCP free
        "cost_private": 15000,   # ₹ 6-month course
        "side_effects": 0.12,
        "time_to_effect_days": 14,
        "qaly_weight": 2.1
    },
    "sputum_afb_test": {
        "cost_govt": 0,
        "cost_private": 150,
        "side_effects": 0.0,
        "time_to_effect_days": 2,
        "qaly_weight": 0.3  # diagnostic value
    },
    "iron_supplement": {
        "cost_govt": 0,          # NRHM free
        "cost_private": 120,     # ₹/month
        "side_effects": 0.05,
        "time_to_effect_days": 14,
        "qaly_weight": 0.8
    },
    "lifestyle_counseling": {
        "cost_govt": 0,
        "cost_private": 500,
        "side_effects": 0.0,
        "time_to_effect_days": 60,
        "qaly_weight": 0.4
    },
    "emergency_108": {
        "cost_govt": 0,
        "cost_private": 0,
        "side_effects": 0.0,
        "time_to_effect_days": 0,
        "qaly_weight": 3.0   # emergency
    }
}
