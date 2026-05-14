# Layer 1 → Layer 2 Feature Schema

**Contract version**: 1.0 | **Date**: 2026-05-14

Defines the exact feature vector that Person 1 (Signal Intelligence) must produce
and Person 2 (Causal AI) consumes as `patient_features`.

---

## Required Feature Keys

All values are `float`. Missing values must be `float('nan')` — not 0 or -1.

### rPPG / Physiological Features (from Layer 1 rPPG engine)

| Key | Unit | Range | Description |
|-----|------|-------|-------------|
| `heart_rate` | BPM | 42–240 | Heart rate from rPPG |
| `spo2` | % | 85–100 | Blood oxygen saturation |
| `hrv_rmssd` | ms | 5–200 | Root mean square of successive IBI differences |
| `hrv_sdnn` | ms | 5–150 | Standard deviation of IBI |
| `lf_hf_ratio` | — | 0.5–10 | LF/HF ratio from rPPG HRV |
| `respiratory_rate` | breaths/min | 4–60 | Respiratory rate from rPPG modulation |
| `rppg_confidence` | — | 0.0–1.0 | Signal quality confidence |

### Audio Features (from Layer 1 acoustic engine)

| Key | Unit | Range | Description |
|-----|------|-------|-------------|
| `cough_tb_prob` | — | 0.0–1.0 | YAMNet+CNN ensemble TB probability |
| `cough_pneumonia_prob` | — | 0.0–1.0 | Pneumonia probability |
| `cough_covid_prob` | — | 0.0–1.0 | COVID probability |
| `cough_asthma_prob` | — | 0.0–1.0 | Asthma probability |
| `cough_copd_prob` | — | 0.0–1.0 | COPD probability |
| `breathing_rate_audio` | breaths/min | 4–60 | Breathing rate from audio |
| `ie_ratio` | — | 0.5–4.0 | Inspiratory:Expiratory ratio |
| `wheeze_severity` | 0–3 | 0=none | Wheeze severity score |
| `crackle_severity` | 0–3 | 0=none | Crackle severity score |
| `jitter_local` | % | 0–5 | Voice jitter |
| `shimmer_local` | % | 0–10 | Voice shimmer |
| `hnr` | dB | -10–40 | Harmonics-to-noise ratio |

### Visual Features (from Layer 1 visual engine)

| Key | Unit | Range | Description |
|-----|------|-------|-------------|
| `jaundice_index` | — | 0.0–1.0 | Scleral jaundice severity score |
| `conjunctival_pallor` | — | 0.0–1.0 | Anemia likelihood from conjunctiva |
| `cyanosis_score` | — | 0.0–1.0 | Lip cyanosis score |
| `dengue_flush_score` | — | 0.0–1.0 | Periorbital redness pattern score |
| `skin_pallor_pct` | % | 0–100 | Facial pallor vs baseline |
| `visual_confidence` | — | 0.0–1.0 | Overall visual module quality |

### IMU / Gait Features (from Layer 1 IMU engine)

| Key | Unit | Range | Description |
|-----|------|-------|-------------|
| `gait_symmetry` | — | 0.0–1.0 | Step symmetry ratio |
| `cadence` | steps/min | 30–160 | Walking cadence |
| `stride_variability` | — | 0.0–1.0 | Step length coefficient of variation |
| `imu_confidence` | — | 0.0–1.0 | IMU capture quality |

### Demographic / Contextual Features (from patient intake)

| Key | Unit | Range | Description |
|-----|------|-------|-------------|
| `age` | years | 0–110 | Patient age |
| `sex_binary` | — | 0 or 1 | 0=female, 1=male |
| `bmi` | kg/m² | 10–50 | Body mass index (or NaN if unknown) |
| `wealth_index` | 1–5 | 1–5 | Household wealth quintile (NFHS scale) |
| `urban_rural` | — | 0 or 1 | 1=urban, 0=rural |
| `crowding_index` | — | 0.5–10 | Persons per room |
| `nutrition_score` | 0–10 | 0–10 | Self-reported/ASHA-assessed nutrition score |
| `smoking_status` | — | 0 or 1 | 1=current smoker |
| `water_quality` | 1–5 | 1–5 | WHO water source classification |

---

## Availability Flags

Layer 1 must also provide modality availability flags:

```python
modality_available: Dict[str, bool] = {
    "rppg": True,
    "audio": True,
    "visual": True,
    "imu": False,   # e.g. if gait capture was skipped
}
```

Features for an unavailable modality must be `float('nan')`.

---

## Validation

Layer 2 accepts the feature dict and validates:
1. At least 3 non-NaN features across ≥2 modalities — otherwise raises `InsufficientFeaturesError`
2. Values within documented range — out-of-range values set to NaN with warning
3. Modality confidence scores < 0.4 → corresponding features set to NaN (low-quality signal)
