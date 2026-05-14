# Tasks: PRISM Layer 1 — SENSE (Person 1: Signal Intelligence Engineer)

**Input**: Design documents from `/specs/001-prism-platform/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, config scaffolding

- [x] T001 Create project directory structure per plan.md — `layer1_sense/`, `layer1_sense/rppg/`, `layer1_sense/audio/`, `layer1_sense/visual/`, `layer1_sense/fusion/`, `layer1_sense/tests/`, `scripts/`, `configs/`, `android_integration/`
- [x] T002 Create `requirements.txt` with pinned versions: mediapipe==0.10.9, opencv-python==4.9.0.80, numpy==1.26.4, scipy==1.13.0, torch==2.1.2, torchaudio==2.1.2, librosa==0.10.1, audiomentations==0.36.0, tensorflow==2.15.0, tensorflow-hub==0.16.0, onnx==1.16.0, onnxruntime==1.17.3, praat-parselmouth, catboost, pytest
- [x] T003 [P] Create `configs/sense_config.yaml` with rPPG parameters (fps, min_duration, hr_range, bandpass, ROIs) and audio parameters (sample_rate, cough thresholds, mel bins)
- [x] T004 [P] Create all `__init__.py` files for `layer1_sense/`, `layer1_sense/rppg/`, `layer1_sense/audio/`, `layer1_sense/visual/`, `layer1_sense/fusion/`
- [x] T005 [P] Create shared dataclass definitions in `layer1_sense/datatypes.py` — VitalsResult, CoughSegment, AcousticFeatures, AudioAnalysisResult, FaceROIs, ColorBiomarkers, VisualBiomarkerResult, SenseResult, VoiceBiomarkers (per data-model.md)
- [x] T006 [P] Create custom exception classes in `layer1_sense/exceptions.py` — FaceNotDetectedError, InsufficientDataError, AudioQualityError, ModelNotLoadedError

**Checkpoint**: Foundation ready — all modality development can begin in parallel.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities used across all modalities. MUST complete before user stories.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T007 Install all dependencies from `requirements.txt` and verify imports work (mediapipe, librosa, torch, tensorflow, tensorflow_hub)
- [ ] T008 [P] Create config loader utility in `layer1_sense/config.py` that reads `configs/sense_config.yaml` and exposes typed config objects
- [ ] T009 [P] Create logging setup in `layer1_sense/logger.py` — structured JSON logging via Python stdlib, configurable log level, no print statements

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel.

---

## Phase 3: User Story 1 — Clinical Diagnostic Scan via Smartphone (Priority: P1) 🎯 MVP

**Goal**: A 30-second smartphone capture (audio + video + IMU) is processed through rPPG, audio, visual, and fusion pipelines to produce multi-disease probabilities with uncertainty bounds — 100% offline.

**Independent Test**: Feed pre-recorded 30-second video/audio → verify output probabilities are valid floats in [0,1], uncertainty bounds are present, processing completes < 500ms on laptop.

### 3A: rPPG Sub-Module

- [ ] T010 [P] [US1] Implement MediaPipe FaceMesh face detection with 3-ROI extraction (forehead, left cheek, right cheek) using specific landmark indices in `layer1_sense/rppg/face_detector.py`
- [ ] T011 [P] [US1] Implement ROI mean-RGB extraction with CLAHE lighting normalization and gray-world white balance correction in `layer1_sense/rppg/roi_extractor.py`
- [ ] T012 [US1] Implement CHROM rPPG signal processing pipeline (linear detrend → moving average subtraction → CHROM method → bandpass 0.7–4.0Hz → SNR-weighted ROI fusion) in `layer1_sense/rppg/signal_processor.py`
- [ ] T013 [US1] Implement vitals estimation (HR via Welch PSD, SpO2 via Beer-Lambert ratio, HRV via peak detection + RMSSD/SDNN/LF-HF, RR via respiratory envelope) in `layer1_sense/rppg/vitals_estimator.py`
- [ ] T014 [US1] Implement end-to-end rPPG pipeline class `PRISMrPPGPipeline` with `process_video()` and `process_frame_stream()` methods, 30-second minimum enforcement, and logging in `layer1_sense/rppg/rppg_pipeline.py`
- [ ] T015 [P] [US1] Write rPPG unit tests in `layer1_sense/tests/test_rppg.py` — synthetic sinusoidal signal → HR ±2 BPM, no-face → FaceNotDetectedError, short video → InsufficientDataError

### 3B: Audio Sub-Module

- [ ] T016 [P] [US1] Implement energy-based cough detector with frequency confirmation and CNN binary classifier (cough vs non-cough) in `layer1_sense/audio/cough_detector.py`
- [ ] T017 [P] [US1] Implement acoustic feature extractor (Mel spectrogram 128 bins, MFCC 40+Δ+ΔΔ=120, Chroma STFT, spectral centroid/rolloff/bandwidth/ZCR/flux, temporal features) in `layer1_sense/audio/feature_extractor.py`
- [ ] T018 [US1] Implement YAMNet fine-tuning wrapper `PRISMCoughHead` (8-class: TB, COVID, Pneumonia, Whooping cough, Asthma, COPD, Healthy, Uncertain) with 1D-CNN ensemble and `predict()` method in `layer1_sense/audio/cough_classifier.py`
- [ ] T019 [P] [US1] Implement breathing analyzer with Hilbert transform envelope segmentation, I:E ratio, wheeze/crackle/stridor binary CNNs, and severity scoring in `layer1_sense/audio/breathing_analyzer.py`
- [ ] T020 [P] [US1] Implement voice biomarker extraction (jitter, shimmer, HNR via parselmouth; RPDE, DFA, PPE; Parkinson's SVM, anemia CatBoost regressor) in `layer1_sense/audio/voice_biomarker.py`
- [ ] T021 [US1] Implement `PRISMAudioPipeline` with `analyze_cough()`, `analyze_breathing()`, `analyze_voice()`, `full_analysis()` (parallel via ThreadPoolExecutor) in `layer1_sense/audio/audio_pipeline.py`
- [ ] T022 [P] [US1] Write audio unit tests in `layer1_sense/tests/test_audio.py` — sine wave → breathing rate, silence → Uncertain class, valid probability output shape

### 3C: Visual Sub-Module

- [ ] T023 [P] [US1] Implement face ROI segmentation (sclera, conjunctiva, lips, skin regions via MediaPipe landmark indices → pixel masks) in `layer1_sense/visual/face_analyzer.py`
- [ ] T024 [US1] Implement color-based biomarker scoring (jaundice via HSV sclera, anemia via conjunctival redness ratio, cyanosis via lip blue dominance, dengue flush via periorbital R-channel, pallor via luminance) in `layer1_sense/visual/color_biomarker.py`
- [ ] T025 [US1] Implement MobileNetV3-Large multi-task classifier with 4 parallel heads (jaundice 4-class, anemia binary, cyanosis binary, dengue binary) and training function in `layer1_sense/visual/disease_classifier.py`
- [ ] T026 [US1] Implement `PRISMVisualPipeline` with `analyze_frame()`, `analyze_video()` (median aggregation), and cross-validation between color_biomarker and classifier outputs in `layer1_sense/visual/visual_pipeline.py`
- [ ] T027 [P] [US1] Write visual unit tests in `layer1_sense/tests/test_visual.py` — synthetic blank frame → no-disease baseline, face-detected frame → valid scores

### 3D: Cross-Modal Attention Fusion

- [ ] T028 [US1] Implement `PRISMFusionModel` (4 modality encoders → 128-dim, learned modality embeddings, MultiheadAttention 4 heads, FFN, sigmoid multi-label classifier for 12 diseases) with missing-modality masking in `layer1_sense/fusion/cross_modal_fusion.py`
- [ ] T029 [US1] Implement fusion training loop with synthetic data generation, MC-Dropout uncertainty (T=20 passes), and temperature scaling calibration in `layer1_sense/fusion/fusion_trainer.py`
- [ ] T030 [US1] Write fusion tests in `layer1_sense/tests/test_fusion.py` — verify output shape (12,) ∈ [0,1], attention weights valid, ablation: fusion ≥ single modality, missing modality doesn't crash

### 3E: End-to-End Integration

- [ ] T031 [US1] Create end-to-end SENSE pipeline class `PRISMSensePipeline` in `layer1_sense/sense_pipeline.py` that orchestrates rPPG + Audio + Visual → Fusion → SenseResult, with parallel execution and total latency logging
- [ ] T032 [US1] Write end-to-end integration test in `layer1_sense/tests/test_e2e.py` — dummy patient data → all 4 pipelines → fusion → assert output shape (12,) probs in [0,1], processing < 500ms on laptop

**Checkpoint**: User Story 1 fully functional. A 30-second capture produces disease probabilities with uncertainty. Independently testable and demoable.

---

## Phase 4: User Story 2 — Causal Intervention and Trajectory Planning (Priority: P2)

**Goal**: Person 1 scope for US2 is limited to exporting the SenseResult contract that Layer 2 (Person 2) and Layer 3 (Person 3) consume. The causal engine and trajectory simulation are owned by Persons 2 and 3.

**Independent Test**: Verify SenseResult JSON serialization matches the interface contract expected by downstream layers.

- [ ] T033 [US2] Add JSON serialization/deserialization methods to all dataclasses in `layer1_sense/datatypes.py` — `to_dict()`, `from_dict()`, `to_json()` for SenseResult → Layer 2/3 interop
- [ ] T034 [US2] Write contract validation test in `layer1_sense/tests/test_contracts.py` — assert SenseResult.to_dict() keys match the exact interface contract: `disease_probabilities`, `rppg`, `audio`, `visual`, `uncertainty`, `processing_time_ms`

**Checkpoint**: Layer 1 output contract validated against Layer 2/3 input expectations.

---

## Phase 5: User Story 3 — ABDM Integration (Priority: P3)

**Goal**: Person 1 scope for US3 is zero — ABDM integration is owned by Person 4. No tasks here.

---

## Phase 6: TFLite Export & Android Deployment

**Purpose**: Export all trained models to TFLite for offline Android inference. Directly supports SC-002, SC-004, FR-008.

- [ ] T035 Implement TFLite export pipeline for YAMNet cough classifier (SavedModel → FP16 TFLite) in `scripts/export_to_tflite.py`
- [ ] T036 Add rPPG signal processor TFLite export (tf.signal-based FFT ops) to `scripts/export_to_tflite.py`
- [ ] T037 Add MobileNetV3 visual classifier export (PyTorch → ONNX → TFLite via onnx-tf) to `scripts/export_to_tflite.py`
- [ ] T038 Add fusion model INT8 quantized export with representative dataset to `scripts/export_to_tflite.py`
- [ ] T039 Implement TFLite benchmark script (100 inference calls, mean/p95 latency, model size, accuracy vs original) in `scripts/benchmark_tflite.py`
- [ ] T040 Create Android integration spec README with method signatures, input/output tensor shapes, and Kotlin code snippets in `android_integration/README.md`
- [ ] T041 Write TFLite validation tests in `layer1_sense/tests/test_tflite.py` — load each .tflite, run inference on test input, verify output matches original model within tolerance

**Checkpoint**: All 4 TFLite models exported and validated. Combined size < 15MB.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Quality, documentation, performance hardening

- [ ] T042 [P] Add docstrings and type hints to all public classes and methods across `layer1_sense/`
- [ ] T043 [P] Create dataset download scripts in `scripts/download_coughvid.py` and `scripts/download_coswara.py`
- [ ] T044 Run `quickstart.md` validation — execute the quickstart example end-to-end and verify it works
- [ ] T045 [P] Add edge case handling: low-light fallback (audio/IMU only), high-noise audio warning, missing modality graceful degradation
- [ ] T046 Profile full pipeline end-to-end and optimize any bottleneck exceeding latency targets (cough < 50ms, rPPG < 100ms, visual < 30ms, fusion < 10ms)
- [ ] T047 Final model size audit — verify combined TFLite models < 15MB per SC-004

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — main body of work
- **US2 (Phase 4)**: Depends on Phase 3 (needs SenseResult definition to be finalized)
- **TFLite Export (Phase 6)**: Depends on Phase 3 (needs trained models)
- **Polish (Phase 7)**: Depends on Phases 3, 4, 6

### Within Phase 3 (US1)

- Sub-modules 3A (rPPG), 3B (Audio), 3C (Visual) are **fully parallel** — no dependencies between them
- Sub-module 3D (Fusion) depends on 3A, 3B, 3C being complete (consumes their outputs)
- Sub-module 3E (E2E) depends on 3D

### Parallel Opportunities

```
Phase 3 parallelism:
├── [PARALLEL] 3A: T010–T015 (rPPG)
├── [PARALLEL] 3B: T016–T022 (Audio)
├── [PARALLEL] 3C: T023–T027 (Visual)
├── [SEQUENTIAL after 3A+3B+3C] 3D: T028–T030 (Fusion)
└── [SEQUENTIAL after 3D] 3E: T031–T032 (E2E)
```

---

## Parallel Example: User Story 1 Sub-Modules

```
# These 3 groups can run simultaneously:
Group A (rPPG):  T010, T011 → T012 → T013 → T014, T015
Group B (Audio): T016, T017 → T018, T019, T020 → T021, T022
Group C (Visual): T023 → T024 → T025 → T026, T027

# After A+B+C complete:
Group D (Fusion): T028 → T029 → T030
Group E (E2E):    T031 → T032
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (rPPG → Audio → Visual → Fusion → E2E)
4. **STOP and VALIDATE**: Feed test audio/video → verify disease probabilities output
5. Demo-ready with basic SENSE capability

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 rPPG only → partial vital signs extraction → demo heartbeat on screen
3. US1 + Audio → cough detection added → demo cough classification
4. US1 + Visual → facial biomarkers → demo jaundice/anemia detection
5. US1 + Fusion → full multi-disease output → primary demo ready
6. TFLite export → offline Android deployment → final demo target

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each sub-module (rPPG, Audio, Visual) is independently testable
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Person 2/3/4 consume `SenseResult` — do not break its contract
