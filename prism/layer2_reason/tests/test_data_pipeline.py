"""T017 - Tests for data pipeline (no MIMIC dependency — synthetic fixtures)."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pickle
import pytest
import tempfile
from pathlib import Path

from layer2_reason.data.data_validator import (
    DataValidationError,
    validate_panel_dataset,
    enforce_physiological_bounds,
    PHYSIOLOGICAL_BOUNDS,
)


# ---------------------------------------------------------------------------
# data_validator tests
# ---------------------------------------------------------------------------

class TestDataValidator:

    def test_valid_panel_passes(self, synthetic_panel_dataset):
        report = validate_panel_dataset(synthetic_panel_dataset, min_patients=5)
        assert report["checks"]["overall"] == "PASS"
        assert report["checks"]["required_columns"] == "PASS"

    def test_missing_column_raises(self, synthetic_panel_dataset):
        bad = synthetic_panel_dataset.drop(columns=["patient_id"])
        with pytest.raises(DataValidationError, match="Missing required columns"):
            validate_panel_dataset(bad)

    def test_too_few_patients_raises(self, synthetic_panel_dataset):
        one_patient = synthetic_panel_dataset[synthetic_panel_dataset["patient_id"] == "P0000"]
        with pytest.raises(DataValidationError, match="patients found"):
            validate_panel_dataset(one_patient, min_patients=10)

    def test_physiological_bounds_enforced(self, synthetic_panel_dataset):
        panel = synthetic_panel_dataset.copy()
        panel.loc[0, "heart_rate"] = 9999.0  # Way out of bounds
        cleaned = enforce_physiological_bounds(panel)
        assert pd.isna(cleaned.loc[0, "heart_rate"])
        # Original unchanged
        assert panel.loc[0, "heart_rate"] == 9999.0

    def test_missing_rate_computed(self, synthetic_panel_dataset):
        # Inject some NaNs
        panel = synthetic_panel_dataset.copy()
        panel.loc[:5, "hemoglobin"] = np.nan
        report = validate_panel_dataset(panel, min_patients=5)
        assert "hemoglobin" in report["statistics"]["missing_rates"]
        assert report["statistics"]["missing_rates"]["hemoglobin"] > 0


# ---------------------------------------------------------------------------
# feature_engineering tests
# ---------------------------------------------------------------------------

class TestFeatureEngineering:

    def test_lag_features_created(self, synthetic_patient_timeseries):
        from layer2_reason.data.feature_engineering import build_panel_dataset, N_LAGS
        with tempfile.TemporaryDirectory() as tmp:
            panel_path = Path(tmp) / "panel.pkl"
            scalers_path = Path(tmp) / "scalers.pkl"
            panel = build_panel_dataset(
                synthetic_patient_timeseries[:5],
                panel_path,
                scalers_path,
            )
        # Check lag columns exist
        assert "hemoglobin_lag1" in panel.columns
        assert f"hemoglobin_lag{N_LAGS}" in panel.columns

    def test_diff_features_created(self, synthetic_patient_timeseries):
        from layer2_reason.data.feature_engineering import build_panel_dataset
        with tempfile.TemporaryDirectory() as tmp:
            panel = build_panel_dataset(
                synthetic_patient_timeseries[:5],
                Path(tmp) / "panel.pkl",
                Path(tmp) / "scalers.pkl",
            )
        assert "hemoglobin_diff" in panel.columns

    def test_rolling_features_created(self, synthetic_patient_timeseries):
        from layer2_reason.data.feature_engineering import build_panel_dataset
        with tempfile.TemporaryDirectory() as tmp:
            panel = build_panel_dataset(
                synthetic_patient_timeseries[:5],
                Path(tmp) / "panel.pkl",
                Path(tmp) / "scalers.pkl",
            )
        assert "hemoglobin_roll_mean" in panel.columns
        assert "hemoglobin_roll_std" in panel.columns

    def test_scaler_persisted(self, synthetic_patient_timeseries):
        from layer2_reason.data.feature_engineering import build_panel_dataset
        with tempfile.TemporaryDirectory() as tmp:
            scalers_path = Path(tmp) / "scalers.pkl"
            build_panel_dataset(
                synthetic_patient_timeseries[:5],
                Path(tmp) / "panel.pkl",
                scalers_path,
            )
        assert scalers_path.exists()
        with open(scalers_path, "rb") as f:
            scalers = pickle.load(f)
        assert "hemoglobin" in scalers

    def test_panel_saved_to_disk(self, synthetic_patient_timeseries):
        from layer2_reason.data.feature_engineering import build_panel_dataset
        with tempfile.TemporaryDirectory() as tmp:
            panel_path = Path(tmp) / "panel.pkl"
            build_panel_dataset(
                synthetic_patient_timeseries[:5],
                panel_path,
                Path(tmp) / "scalers.pkl",
            )
        assert panel_path.exists()
