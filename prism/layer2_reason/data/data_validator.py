"""T007 - Data validator for MIMIC-IV preprocessor output."""
from __future__ import annotations

import logging
from typing import Dict, List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

PHYSIOLOGICAL_BOUNDS: Dict[str, tuple] = {
    "hemoglobin": (3.0, 20.0),
    "wbc": (0.5, 100.0),
    "creatinine": (0.1, 20.0),
    "temperature": (32.0, 42.5),
    "heart_rate": (20.0, 300.0),
    "spo2": (50.0, 100.0),
    "respiratory_rate": (4.0, 60.0),
    "sbp": (50.0, 250.0),
    "glucose": (20.0, 600.0),
    "crp": (0.0, 500.0),
    "bilirubin_total": (0.1, 50.0),
    "platelet": (5.0, 1500.0),
}

REQUIRED_COLUMNS = ["time_hours", "patient_id", "disease_label"] + list(PHYSIOLOGICAL_BOUNDS)


class DataValidationError(Exception):
    """Raised when the dataset fails validation checks."""


def validate_panel_dataset(panel: pd.DataFrame, min_patients: int = 10) -> Dict:
    """Validate a panel dataset and return a validation report.

    Parameters
    ----------
    panel : pd.DataFrame
        Flat panel (rows = patient×timepoint; columns = biomarkers + metadata).
    min_patients : int
        Minimum required patients for a valid dataset.

    Returns
    -------
    Dict
        Validation report with pass/fail per check and statistics.

    Raises
    ------
    DataValidationError
        If critical checks fail (missing required columns, too few patients).
    """
    report: Dict = {"checks": {}, "statistics": {}, "warnings": []}

    # --- Required columns ---
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in panel.columns]
    if missing_cols:
        raise DataValidationError(f"Missing required columns: {missing_cols}")
    report["checks"]["required_columns"] = "PASS"

    # --- Patient count ---
    n_patients = panel["patient_id"].nunique()
    if n_patients < min_patients:
        raise DataValidationError(
            f"Only {n_patients} patients found; minimum is {min_patients}"
        )
    report["checks"]["min_patients"] = "PASS"
    report["statistics"]["n_patients"] = n_patients
    report["statistics"]["n_rows"] = len(panel)

    # --- Physiological bounds ---
    outlier_rates: Dict[str, float] = {}
    for bm, (lo, hi) in PHYSIOLOGICAL_BOUNDS.items():
        if bm not in panel.columns:
            continue
        col = panel[bm].dropna()
        if len(col) == 0:
            continue
        out_of_bounds = ((col < lo) | (col > hi)).sum()
        rate = out_of_bounds / len(col)
        outlier_rates[bm] = float(rate)
        if rate > 0.05:
            report["warnings"].append(
                f"{bm}: {rate:.1%} of values outside physiological bounds "
                f"[{lo}, {hi}] — flagged as outliers"
            )
    report["checks"]["physiological_bounds"] = "PASS"
    report["statistics"]["outlier_rates"] = outlier_rates

    # --- Missing rates ---
    missing_rates: Dict[str, float] = {}
    for bm in PHYSIOLOGICAL_BOUNDS:
        if bm not in panel.columns:
            continue
        rate = float(panel[bm].isna().mean())
        missing_rates[bm] = rate
        if rate > 0.5:
            report["warnings"].append(f"{bm}: {rate:.1%} missing values (high)")
    report["statistics"]["missing_rates"] = missing_rates

    # --- Disease label distribution ---
    if "disease_label" in panel.columns:
        counts = panel.drop_duplicates("patient_id")["disease_label"].value_counts().to_dict()
        report["statistics"]["disease_counts"] = counts
        logger.info("Disease cohort sizes: %s", counts)

    report["checks"]["overall"] = "PASS"
    logger.info(
        "Validation PASSED | patients=%d rows=%d warnings=%d",
        n_patients, len(panel), len(report["warnings"]),
    )
    return report


def enforce_physiological_bounds(panel: pd.DataFrame) -> pd.DataFrame:
    """Set out-of-range biomarker values to NaN (non-destructive copy)."""
    panel = panel.copy()
    for bm, (lo, hi) in PHYSIOLOGICAL_BOUNDS.items():
        if bm not in panel.columns:
            continue
        mask = (panel[bm] < lo) | (panel[bm] > hi)
        panel.loc[mask, bm] = np.nan
    return panel
