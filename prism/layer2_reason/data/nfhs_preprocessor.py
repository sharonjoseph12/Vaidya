"""T009 - NFHS-5 preprocessor: extract India-specific socioeconomic features."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

NFHS_FIELD_MAP = {
    "hv237": "food_security",
    "hml32": "malnutrition_zscore",
    "hb56": "hemoglobin",
    "hb57": "anemia_level",
    "hv270": "wealth_index",
    "hv025": "urban_rural",
    "hv201": "water_source",
    "hv205": "sanitation_type",
    "hv216": "n_rooms",
    "hv009": "n_household_members",
}
TB_SYMPTOM_COLS = ["s103a", "s103b", "s103c", "s103d", "s103e"]


def preprocess_nfhs(input_dir: str | Path, output_path: str | Path) -> pd.DataFrame:
    """Preprocess NFHS-5 survey data into ML-ready feature DataFrame.

    Parameters
    ----------
    input_dir : directory containing NFHS-5 CSV/DTA files
    output_path : path to save pickled output DataFrame
    """
    input_dir = Path(input_dir)
    output_path = Path(output_path)

    # NFHS-5 can be in DTA or CSV format
    csv_files = list(input_dir.glob("*.csv"))
    dta_files = list(input_dir.glob("*.DTA")) + list(input_dir.glob("*.dta"))

    if csv_files:
        df = pd.concat([pd.read_csv(f, low_memory=False) for f in csv_files], ignore_index=True)
    elif dta_files:
        df = pd.concat([pd.read_stata(f) for f in dta_files], ignore_index=True)
    else:
        raise FileNotFoundError(f"No NFHS CSV or DTA files found in {input_dir}")

    logger.info("Loaded NFHS-5 data: %d rows, %d columns", len(df), len(df.columns))

    # Lowercase all column names
    df.columns = [c.lower() for c in df.columns]

    out = pd.DataFrame()

    # --- Rename base fields ---
    for src, dst in NFHS_FIELD_MAP.items():
        if src in df.columns:
            out[dst] = pd.to_numeric(df[src], errors="coerce")
        else:
            logger.warning("NFHS field %s not found — setting to NaN", src)
            out[dst] = np.nan

    # --- TB symptom score ---
    symptom_cols = [c for c in TB_SYMPTOM_COLS if c in df.columns]
    if symptom_cols:
        out["tb_symptom_score"] = df[symptom_cols].apply(
            pd.to_numeric, errors="coerce"
        ).sum(axis=1)
    else:
        out["tb_symptom_score"] = np.nan

    # --- Derived features ---
    if "n_household_members" in out.columns and "n_rooms" in out.columns:
        out["crowding_index"] = out["n_household_members"] / out["n_rooms"].replace(0, np.nan)
    else:
        out["crowding_index"] = np.nan

    # Anemia binary: Hb < 11 (women/children) — simplified
    if "hemoglobin" in out.columns:
        # NFHS stores Hb in g/dL × 10 in some versions
        hb = out["hemoglobin"].copy()
        if hb.median() > 30:  # likely stored as ×10
            hb = hb / 10.0
        out["hemoglobin_gdl"] = hb
        out["anemia_binary"] = (hb < 12.0).astype(float)
    else:
        out["anemia_binary"] = np.nan

    # Composite nutrition score (0–10): weighted food_security + malnutrition
    if "food_security" in out.columns:
        fs = pd.to_numeric(out["food_security"], errors="coerce").fillna(5)
        mz = pd.to_numeric(out.get("malnutrition_zscore", pd.Series([0] * len(out))),
                           errors="coerce").fillna(0)
        # Map to 0–10 scale
        out["nutrition_score"] = (fs / fs.max() * 7 + (mz.clip(-3, 0) + 3) / 3 * 3).clip(0, 10)

    # Drop intermediate helper columns
    out = out.drop(columns=["n_rooms", "n_household_members"], errors="ignore")

    logger.info("NFHS preprocessing complete | rows=%d features=%s", len(out), list(out.columns))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(out, f)
    logger.info("Saved NFHS features to %s", output_path)
    return out


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess NFHS-5 data")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    preprocess_nfhs(args.input, args.output)
