# PRISM SENSE Layer — Quickstart Guide

## Prerequisites

- Python 3.11+
- `uv` package manager (recommended)

## Setup

```bash
# Clone and setup
cd Vaidya
uv venv .venv --python 3.11
.venv/Scripts/activate   # Windows
# source .venv/bin/activate  # Linux/Mac

uv pip install -r requirements.txt
```

## Quick Test — Run All Unit Tests

```bash
pytest layer1_sense/tests/ -v
```

Expected: 24 tests passing across rPPG, audio, visual, fusion, E2E, contracts, and TFLite modules.

## Programmatic Usage

### 1. Individual Modalities

```python
import numpy as np
from layer1_sense.rppg.signal_processor import PRISMrPPGProcessor
from layer1_sense.audio.cough_detector import PRISMCoughDetector
from layer1_sense.visual.color_biomarker import PRISMColorBiomarker

# rPPG: process RGB signals from face video
processor = PRISMrPPGProcessor(fps=30)
rgb_signal = np.random.randn(900, 3)  # 30 seconds @ 30fps
bvp = processor.chrom_method(rgb_signal)

# Audio: detect coughs
detector = PRISMCoughDetector(sample_rate=16000)
audio = np.random.randn(16000 * 5)  # 5 seconds
segments = detector.detect_coughs(audio)

# Visual: score color biomarkers
from layer1_sense.datatypes import FaceROIs
rois = FaceROIs(
    forehead=np.random.randint(0, 255, (500, 3), dtype=np.uint8),
    left_cheek=np.random.randint(0, 255, (500, 3), dtype=np.uint8),
    right_cheek=np.random.randint(0, 255, (500, 3), dtype=np.uint8),
    sclera=np.random.randint(0, 255, (200, 3), dtype=np.uint8),
    conjunctiva=np.random.randint(0, 255, (200, 3), dtype=np.uint8),
    lips=np.random.randint(0, 255, (300, 3), dtype=np.uint8),
)
scorer = PRISMColorBiomarker()
biomarkers = scorer.analyze(rois)
print(f"Jaundice: {biomarkers.jaundice_score:.2f} ({biomarkers.jaundice_severity})")
```

### 2. Full SENSE Pipeline

```python
from layer1_sense.sense_pipeline import PRISMSensePipeline

pipeline = PRISMSensePipeline(fps=30, sample_rate=16000)

# Run with video + audio
result = pipeline.run(
    video_path="patient_recording.mp4",
    audio_path="patient_cough.wav",
)

# Access results
print(result.disease_probabilities)
print(f"HR: {result.rppg.hr} bpm, SpO2: {result.rppg.spo2}%")
print(f"Cough detected: {result.audio.cough_detected}")
print(f"Jaundice: {result.visual.color_biomarkers.jaundice_severity}")

# Serialize for Layer 2/3
json_output = result.to_json()
print(json_output)
```

### 3. Fusion Model Only

```python
import torch
from layer1_sense.fusion.cross_modal_fusion import PRISMFusionModel

model = PRISMFusionModel()
model.eval()

# Fake features
rppg_feat = torch.randn(1, 7)
audio_feat = torch.randn(1, 16)
visual_feat = torch.randn(1, 11)

# Predict with uncertainty
mean_probs, std_probs = model.predict_with_uncertainty(
    rppg_feat, audio_feat, visual_feat, n_passes=20
)

for i, name in enumerate(PRISMFusionModel.DISEASES):
    print(f"  {name}: {mean_probs[0,i]:.3f} ± {std_probs[0,i]:.3f}")
```

## Export Models for Android

```bash
python scripts/export_to_tflite.py
python scripts/benchmark_tflite.py
```

See `android_integration/README.md` for Kotlin integration details.

## Download Training Datasets

```bash
python scripts/download_coughvid.py
python scripts/download_coswara.py
```
