"""T008 - MIMIC-IV preprocessor: extract patient biomarker timeseries."""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

BIOMARKER_ITEMIDS: Dict[str, int] = {
    "hemoglobin": 51222, "wbc": 51301, "creatinine": 50912,
    "temperature": 223762, "heart_rate": 220045, "spo2": 220277,
    "respiratory_rate": 220210, "sbp": 220179, "glucose": 220621,
    "crp": 50889, "bilirubin_total": 50885, "platelet": 51265,
}

DISEASE_ICD10: Dict[str, List[str]] = {
    "tb": ["A15", "A16", "A17", "A18", "A19"],
    "pneumonia": ["J12", "J13", "J14", "J15", "J16", "J17", "J18"],
    "sepsis": ["A40", "A41"],
    "heart_failure": ["I50"],
    "anemia": ["D50", "D51", "D52", "D53", "D64"],
    "dengue": ["A90", "A91"],
}


def _extract_labels(diagnoses: pd.DataFrame, hadm_ids: pd.Series) -> Dict[str, List[str]]:
    """Map hospital admission IDs to disease name lists via ICD-10 codes."""
    diag = diagnoses[diagnoses["hadm_id"].isin(hadm_ids)]
    result: Dict[str, List[str]] = {}
    for _, row in diag.iterrows():
        hadm = str(row["hadm_id"])
        icd = str(row.get("icd_code", "")).upper()
        matched = [
            disease for disease, prefixes in DISEASE_ICD10.items()
            if any(icd.startswith(p) for p in prefixes)
        ]
        if matched:
            result.setdefault(hadm, []).extend(matched)
    # Deduplicate
    return {k: list(set(v)) for k, v in result.items()}


def _handle_missing(series: pd.Series, time_hours: pd.Series) -> pd.Series:
    """Apply gap-aware missing value strategy."""
    s = series.copy()
    # Compute time gaps between observations
    sorted_idx = time_hours.argsort()
    s_sorted = s.iloc[sorted_idx].reset_index(drop=True)
    t_sorted = time_hours.iloc[sorted_idx].reset_index(drop=True)
    for i in range(1, len(s_sorted)):
        gap = t_sorted.iloc[i] - t_sorted.iloc[i - 1]
        if pd.isna(s_sorted.iloc[i]):
            if gap <= 4:
                # Linear interpolation: fill with previous + slope
                s_sorted.iloc[i] = s_sorted.iloc[i - 1]  # simplified; full interp below
            elif gap <= 12:
                s_sorted.iloc[i] = s_sorted.iloc[i - 1]  # forward fill
            # else: leave as NaN
    # Proper interpolation pass (linear for <4h gaps)
    s_out = s_sorted.interpolate(method="linear", limit=4)
    # Forward fill remaining short gaps
    s_out = s_out.ffill(limit=12)
    return s_out


def preprocess_mimic(
    mimic_dir: str | Path,
    output_path: str | Path,
    min_hours: int = 48,
    min_readings: int = 5,
) -> List[Dict]:
    """Preprocess MIMIC-IV CSVs into patient biomarker timeseries.

    Parameters
    ----------
    mimic_dir : path to MIMIC-IV CSV directory
    output_path : path to save pickled output list
    min_hours : minimum hours of data required per patient
    min_readings : minimum distinct biomarker readings required

    Returns
    -------
    List of patient dicts
    """
    mimic_dir = Path(mimic_dir)
    output_path = Path(output_path)

    logger.info("Loading MIMIC-IV tables from %s", mimic_dir)
    admissions = pd.read_csv(mimic_dir / "admissions.csv.gz", compression="gzip",
                             usecols=["hadm_id", "subject_id", "admittime"])
    patients = pd.read_csv(mimic_dir / "patients.csv.gz", compression="gzip",
                           usecols=["subject_id", "gender", "anchor_age"])
    diagnoses = pd.read_csv(mimic_dir / "diagnoses_icd.csv.gz", compression="gzip",
                            usecols=["hadm_id", "icd_code"])

    # Load lab events (large — chunk)
    labevents_chunks = pd.read_csv(
        mimic_dir / "labevents.csv.gz", compression="gzip",
        usecols=["hadm_id", "itemid", "charttime", "valuenum"],
        chunksize=500_000,
    )
    lab_df = pd.concat(
        [c[c["itemid"].isin(BIOMARKER_ITEMIDS.values())] for c in labevents_chunks],
        ignore_index=True,
    )

    # Map itemid → biomarker name
    itemid_to_name = {v: k for k, v in BIOMARKER_ITEMIDS.items()}
    lab_df["biomarker"] = lab_df["itemid"].map(itemid_to_name)
    lab_df["charttime"] = pd.to_datetime(lab_df["charttime"])

    # Extract disease labels per hadm_id
    labels_map = _extract_labels(diagnoses, admissions["hadm_id"])

    # Merge admittime for relative time computation
    lab_df = lab_df.merge(
        admissions[["hadm_id", "admittime", "subject_id"]],
        on="hadm_id", how="left"
    )
    lab_df["admittime"] = pd.to_datetime(lab_df["admittime"])
    lab_df["time_hours"] = (lab_df["charttime"] - lab_df["admittime"]).dt.total_seconds() / 3600

    # Patient demographic lookup
    pt_info = patients.set_index("subject_id")

    processed: List[Dict] = []
    for hadm_id, grp in lab_df.groupby("hadm_id"):
        # Filter time range
        grp = grp[grp["time_hours"] >= 0]
        if grp["time_hours"].max() < min_hours:
            continue
        if grp["biomarker"].nunique() < min_readings:
            continue

        # Pivot to timeseries
        pivot = grp.pivot_table(
            index="time_hours", columns="biomarker", values="valuenum", aggfunc="mean"
        ).reset_index()

        # Add missing biomarker columns
        for bm in BIOMARKER_ITEMIDS:
            if bm not in pivot.columns:
                pivot[bm] = np.nan

        # Apply missing value strategy per biomarker
        for bm in BIOMARKER_ITEMIDS:
            if bm in pivot.columns:
                pivot[bm] = _handle_missing(pivot[bm], pivot["time_hours"])

        # Demographics
        subject_id = grp["subject_id"].iloc[0]
        demo: Dict = {"age": np.nan, "sex_binary": np.nan, "bmi": np.nan, "admission_weight": np.nan}
        if subject_id in pt_info.index:
            row = pt_info.loc[subject_id]
            demo["age"] = float(row.get("anchor_age", np.nan))
            demo["sex_binary"] = 1.0 if str(row.get("gender", "")).upper() == "M" else 0.0

        disease_names = labels_map.get(str(hadm_id), [])
        processed.append({
            "patient_id": str(hadm_id),
            "timeseries": pivot,
            "labels": disease_names,
            "disease_names": disease_names,
            "demographics": demo,
            "missing_rate": {bm: float(pivot[bm].isna().mean()) for bm in BIOMARKER_ITEMIDS},
        })

    logger.info(
        "Preprocessing complete | patients=%d per_disease=%s",
        len(processed),
        {d: sum(d in p["disease_names"] for p in processed) for d in DISEASE_ICD10},
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(processed, f)
    logger.info("Saved to %s", output_path)
    return processed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess MIMIC-IV data")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--min-hours", type=int, default=48)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    preprocess_mimic(args.input, args.output, args.min_hours)
