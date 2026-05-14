# Implementation Plan: PRISM Layer 1 (SENSE)

**Branch**: `001-prism-platform` | **Date**: 2026-05-14 | **Spec**: [spec.md](../spec.md)
**Input**: Feature specification from `/specs/001-prism-platform/spec.md` and Person 1 build prompts.

## Summary

Build Layer 1: SENSE of the PRISM platform. This involves building a multimodal machine learning pipeline that extracts physiological signals (rPPG), acoustic biomarkers (cough, breathing, voice), and visual biomarkers (facial cues, IMU gait) from a 30-second smartphone capture. It fuses these modalities using a Cross-Modal Attention network and exports all models to quantized TFLite formats for offline, on-device Android inference.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: mediapipe==0.10.9, opencv-python==4.9.0.80, numpy==1.26.4, scipy==1.13.0, torch==2.1.2, torchaudio==2.1.2, librosa==0.10.1, audiomentations==0.36.0, tensorflow==2.15.0, tensorflow-hub==0.16.0, onnx==1.16.0, onnxruntime==1.17.3
**Storage**: N/A (stateless inference pipeline)
**Testing**: pytest
**Target Platform**: Android (via TFLite), Linux (training)
**Project Type**: Machine Learning Edge Pipeline
**Performance Goals**: cough classifier < 50ms, rPPG < 100ms, visual < 30ms, fusion < 10ms. Full pipeline < 500ms on a mid-range device.
**Constraints**: 100% offline-capable, model size < 15MB, 30-second capture minimum.
**Scale/Scope**: Fusion supports 12 target diseases.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Library-First**: Core pipelines (audio, visual, rppg, fusion) are designed as standalone, testable libraries. PASS.
- **CLI/API Interface**: Exposes a unified `PRISMSenseModule` interface for integration. PASS.
- **Test-First**: Test cases are defined for each module (e.g., synthetic signal tests, no-face detection). PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-prism-platform/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (to be generated)
```

### Source Code (repository root)

```text
layer1_sense/
├── __init__.py
├── rppg/
│   ├── __init__.py
│   ├── face_detector.py
│   ├── roi_extractor.py
│   ├── signal_processor.py
│   ├── vitals_estimator.py
│   └── rppg_pipeline.py
├── audio/
│   ├── __init__.py
│   ├── cough_detector.py
│   ├── feature_extractor.py
│   ├── cough_classifier.py
│   ├── breathing_analyzer.py
│   ├── voice_biomarker.py
│   └── audio_pipeline.py
├── visual/
│   ├── __init__.py
│   ├── face_analyzer.py
│   ├── color_biomarker.py
│   ├── disease_classifier.py
│   └── visual_pipeline.py
├── fusion/
│   ├── __init__.py
│   ├── cross_modal_fusion.py
│   └── fusion_trainer.py
└── tests/
    ├── test_rppg.py
    ├── test_audio.py
    ├── test_visual.py
    └── test_fusion.py

scripts/
├── export_to_tflite.py
└── benchmark_tflite.py

configs/
└── sense_config.yaml

android_integration/
└── PRISMAndroidModule.kt
```

**Structure Decision**: A modular python package `layer1_sense` divided by sensory modality, ensuring independent testing and development. Fusion is a separate module that takes extracted embeddings. Android code goes into an `android_integration` folder acting as the deployment target.

## Complexity Tracking

N/A - Project strictly adheres to required architectures and does not violate constitution limits.
