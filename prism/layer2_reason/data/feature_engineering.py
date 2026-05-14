"""T010 - Feature engineering: lag features, rolling stats, normalization."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

BIOMARKERS = [
    "hemoglobin", "wbc", "creatinine", "temperature", "heart_rate",
    "spo2", "respiratory_rate", "sbp", "glucose", "crp",
    "bilirubin_total", "platelet",
]

N_LAGS = 20
LAG_INTERVAL_H = 6
ROLLING_WINDOW_H = 24


def build_panel_dataset(
    patients: List[Dict],
    output_path: str | Path,
    scalers_path: str | Path,
) -> pd.DataFrame:
    """Build flat panel dataset with lag features and rolling statistics.

    Parameters
    ----------
    patients : list of patient dicts from mimic_preprocessor
    output_path : where to save the panel pickle
    scalers_path : where to save per-biomarker StandardScaler pickles

    Returns
    -------
    pd.DataFrame  — shape (n_total_rows, n_features)
    """
    rows = []
    for p in patients:
        df = p["timeseries"].copy()
        df["patient_id"] = p["patient_id"]
        df["disease_label"] = p["disease_names"][0] if p["disease_names"] else "healthy"
        for k, v in p["demographics"].items():
            df[k] = v
        rows.append(df)

    panel = pd.concat(rows, ignore_index=True)
    panel = panel.sort_values(["patient_id", "time_hours"]).reset_index(drop=True)

    logger.info("Base panel: %d rows, %d patients", len(panel), panel["patient_id"].nunique())

    # --- Per-biomarker lag features ---
    for bm in BIOMARKERS:
        if bm not in panel.columns:
            continue
        for lag in range(1, N_LAGS + 1):
            col_name = f"{bm}_lag{lag}"
            panel[col_name] = (
                panel.groupby("patient_id")[bm]
                .shift(lag)
            )

    # --- First differences ---
    for bm in BIOMARKERS:
        if bm not in panel.columns:
            continue
        panel[f"{bm}_diff"] = panel.groupby("patient_id")[bm].diff()

    # --- Rolling statistics (approximate: use row-based window per patient) ---
    roll_steps = max(1, ROLLING_WINDOW_H // LAG_INTERVAL_H)
    for bm in BIOMARKERS:
        if bm not in panel.columns:
            continue
        grp = panel.groupby("patient_id")[bm]
        panel[f"{bm}_roll_mean"] = grp.transform(lambda x: x.rolling(roll_steps, min_periods=1).mean())
        panel[f"{bm}_roll_std"] = grp.transform(lambda x: x.rolling(roll_steps, min_periods=1).std())
        panel[f"{bm}_roll_max"] = grp.transform(lambda x: x.rolling(roll_steps, min_periods=1).max())

    # --- Normalize biomarker columns ---
    scalers: Dict[str, StandardScaler] = {}
    for bm in BIOMARKERS:
        if bm not in panel.columns:
            continue
        scaler = StandardScaler()
        valid_mask = panel[bm].notna()
        if valid_mask.sum() > 0:
            panel.loc[valid_mask, bm] = scaler.fit_transform(
                panel.loc[valid_mask, bm].values.reshape(-1, 1)
            ).ravel()
        scalers[bm] = scaler

    logger.info(
        "Feature engineering complete | cols=%d biomarkers=%d",
        len(panel.columns), len(BIOMARKERS),
    )

    # Save
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(panel, f)

    scalers_path = Path(scalers_path)
    scalers_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scalers_path, "wb") as f:
        pickle.dump(scalers, f)

    logger.info("Panel saved to %s, scalers saved to %s", output_path, scalers_path)
    return panel


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--save-scalers", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    with open(args.input, "rb") as f:
        patients = pickle.load(f)
    build_panel_dataset(patients, args.output, args.save_scalers)
