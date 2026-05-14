import pytest
from layer4_rl.intervention_ranker import rank_interventions

def test_rank_interventions_output():
    top3 = rank_interventions(disease_prob=0.8, patient_income=5000)
    assert len(top3) == 3
    for item in top3:
        assert "name" in item
        assert "score" in item
        assert "free" in item
        assert item["score"] > 0

def test_ranking_logic_low_income():
    # For very low income, free treatments should dominate
    top3 = rank_interventions(disease_prob=0.9, patient_income=1000)
    # Check that the top one is free (in our DB, cost 0 ones should have much higher scores)
    assert top3[0]["free"] is True

def test_ranking_logic_high_disease_prob():
    top3_high = rank_interventions(disease_prob=0.9, patient_income=10000)
    top3_low = rank_interventions(disease_prob=0.1, patient_income=10000)
    
    # Score should be proportional to disease probability
    assert top3_high[0]["score"] > top3_low[0]["score"]
