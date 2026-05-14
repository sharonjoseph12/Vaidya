"""T020 - SCM Builder: fit structural causal models from causal graph."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)


class SCMBuilder:
    """Fit Structural Causal Models from a validated causal graph.

    For each node X_i: fits X_i = f_i(PA_i) + noise_i
    where PA_i = causal parents from graph.

    Parameters
    ----------
    mode : 'production' (GBM) or 'debug' (LinearRegression)
    """

    def __init__(self, mode: Literal["production", "debug"] = "production") -> None:
        self.mode = mode
        self.node_models: Dict[str, Any] = {}
        self.noise_params: Dict[str, Tuple[float, float]] = {}
        self.r2_scores: Dict[str, float] = {}

    def _make_model(self):
        if self.mode == "production":
            return GradientBoostingRegressor(n_estimators=100, max_depth=3, random_state=42)
        return LinearRegression()

    def fit(
        self,
        panel: pd.DataFrame,
        graph,  # nx.DiGraph
        feature_cols: Optional[List[str]] = None,
    ) -> "SCMBuilder":
        """Fit SCM node functions from panel data.

        Parameters
        ----------
        panel : flat panel DataFrame
        graph : networkx DiGraph (causal structure)
        feature_cols : columns to treat as potential parent nodes
        """
        import networkx as nx

        if feature_cols is None:
            feature_cols = [c for c in panel.columns
                            if c not in ("patient_id", "disease_label", "time_hours")]

        panel_clean = panel.dropna(subset=feature_cols)
        if len(panel_clean) < 20:
            raise ValueError(f"Too few complete rows for SCM fitting: {len(panel_clean)}")

        for node in graph.nodes():
            if node not in panel_clean.columns:
                logger.debug("Skipping node %s — not in panel columns", node)
                continue

            parents = [p for p in graph.predecessors(node) if p in panel_clean.columns]
            y = panel_clean[node].values

            if len(parents) == 0:
                # Root node: no parents, model as marginal
                self.noise_params[node] = (float(np.mean(y)), float(np.std(y)))
                self.r2_scores[node] = 0.0
                continue

            X = panel_clean[parents].values
            model = self._make_model()
            try:
                model.fit(X, y)
                y_pred = model.predict(X)
                residuals = y - y_pred
                self.node_models[node] = (model, parents)
                self.noise_params[node] = (float(np.mean(residuals)), float(np.std(residuals)))
                self.r2_scores[node] = float(r2_score(y, y_pred))
                logger.debug("Fitted SCM node %s | parents=%s R²=%.3f", node, parents, self.r2_scores[node])
            except Exception as exc:
                logger.warning("SCM fitting failed for node %s: %s", node, exc)

        logger.info(
            "SCM fitting complete | mode=%s nodes=%d mean_R²=%.3f",
            self.mode,
            len(self.node_models),
            float(np.mean(list(self.r2_scores.values()))) if self.r2_scores else 0.0,
        )
        return self

    def predict_node(self, node: str, parent_values: Dict[str, float]) -> float:
        """Predict the value of a node given parent values."""
        if node not in self.node_models:
            if node in self.noise_params:
                return self.noise_params[node][0]
            return float("nan")
        model, parents = self.node_models[node]
        x = np.array([[parent_values.get(p, np.nan) for p in parents]])
        return float(model.predict(x)[0])

    def save(self, path: str | Path) -> None:
        """Pickle the fitted SCM to disk."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({
                "node_models": self.node_models,
                "noise_params": self.noise_params,
                "r2_scores": self.r2_scores,
                "mode": self.mode,
            }, f)
        logger.info("SCM saved to %s", path)

    @classmethod
    def load(cls, path: str | Path) -> "SCMBuilder":
        """Load a pickled SCM."""
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(mode=data["mode"])
        obj.node_models = data["node_models"]
        obj.noise_params = data["noise_params"]
        obj.r2_scores = data["r2_scores"]
        return obj


def fit_disease_scms(
    panel: pd.DataFrame,
    graphs: Dict,  # Dict[disease, nx.DiGraph]
    output_dir: str | Path,
    mode: str = "production",
) -> Dict[str, SCMBuilder]:
    """Fit SCMs for all disease cohorts and save to disk."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    scms: Dict[str, SCMBuilder] = {}
    for disease, graph in graphs.items():
        cohort = panel[panel.get("disease_label", pd.Series()) == disease] \
            if "disease_label" in panel.columns else panel
        if len(cohort) < 20:
            cohort = panel  # fall back to full panel
        logger.info("Fitting %s SCM on %d rows", disease, len(cohort))
        builder = SCMBuilder(mode=mode)
        builder.fit(cohort, graph)
        builder.save(output_dir / f"{disease}_scm.pkl")
        scms[disease] = builder
    return scms
