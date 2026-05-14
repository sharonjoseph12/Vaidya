"""T029 - Counterfactual Ranker."""
from __future__ import annotations

import logging
from typing import Any, List

logger = logging.getLogger(__name__)


def rank_counterfactuals(cfs: List[Any]) -> List[Any]:
    """Rank counterfactual explanations based on feasibility and impact.
    
    Composite score = 0.5 * feasibility + 0.3 * impact + 0.2 * (1 / n_changes)
    """
    if not cfs:
        return []
        
    def _score(cf: Any) -> float:
        # Avoid division by zero
        n_chg = max(1, cf.n_features_changed)
        return 0.5 * cf.feasibility_score + 0.3 * cf.probability_reduction + 0.2 * (1.0 / n_chg)
        
    scored = [(cf, _score(cf)) for cf in cfs]
    scored.sort(key=lambda x: x[1], reverse=True)
    
    ranked_cfs = []
    for rank, (cf, _score_val) in enumerate(scored, 1):
        cf.rank = rank
        ranked_cfs.append(cf)
        
    return ranked_cfs
