# PRISM — Complete Cursor Build Prompts
## Team of 4 | All Phases | Paste-Ready

---

## TEAM ASSIGNMENT

| Person | Role | Layers |
|--------|------|--------|
| Person 1 | Signal Intelligence Engineer | Layer 1: SENSE (Audio + rPPG + Visual + Fusion) |
| Person 2 | Causal AI Engineer | Layer 2: REASON (Causal Discovery + SCM + Counterfactuals) |
| Person 3 | Deep Learning Engineer | Layer 3+4: Digital Twin + RL Optimizer |
| Person 4 | Platform Engineer | Backend + Frontend + ABDM + FL + Android |

**Integration point: End of every month, all 4 merge to `dev` branch. Person 4 owns integration.**

---

# PERSON 1: SIGNAL INTELLIGENCE ENGINEER
## Layer 1 — SENSE (Acoustic + rPPG + Visual + IMU Fusion)

---

### PHASE 1.1 — PROJECT SETUP + rPPG ENGINE

```
You are building PRISM, a production-grade multimodal medical diagnostic platform. 
You are Person 1 — Signal Intelligence Engineer responsible for Layer 1: SENSE.

TASK: Set up the complete project structure and build the rPPG (Remote 
Photoplethysmography) engine that extracts heart rate, SpO2, HRV, and 
respiratory rate from a phone camera video — no contact sensors.

PROJECT STRUCTURE to create:
prism/
├── layer1_sense/
│   ├── __init__.py
│   ├── rppg/
│   │   ├── __init__.py
│   │   ├── face_detector.py
│   │   ├── roi_extractor.py
│   │   ├── signal_processor.py
│   │   ├── vitals_estimator.py
│   │   └── rppg_pipeline.py
│   ├── audio/
│   ├── visual/
│   ├── imu/
│   ├── fusion/
│   └── tests/
├── requirements.txt
└── configs/
    └── sense_config.yaml

REQUIREMENTS.TXT (exact versions):
mediapipe==0.10.9
opencv-python==4.9.0.80
numpy==1.26.4
scipy==1.13.0
torch==2.1.2
torchaudio==2.1.2
librosa==0.10.1
audiomentations==0.36.0
tensorflow==2.15.0
tensorflow-hub==0.16.0
onnx==1.16.0
onnxruntime==1.17.3

BUILD face_detector.py:
- Use MediaPipe FaceMesh with static_image_mode=False, max_num_faces=1, 
  refine_landmarks=True, min_detection_confidence=0.7
- Extract exactly 3 ROIs: forehead (landmarks 10,338,297,332,284), 
  left cheek (landmarks 116,123,147,213,192), 
  right cheek (landmarks 345,352,376,433,411)
- Return ROI masks as numpy arrays per frame
- Handle: no face detected → raise FaceNotDetectedError with message

BUILD roi_extractor.py:
- Input: video frame (H,W,3 numpy), face landmarks from MediaPipe
- Extract mean RGB per ROI per frame
- Apply CLAHE (cv2.createCLAHE, clipLimit=2.0, tileGridSize=(8,8)) 
  on each ROI before extraction for lighting normalization
- White balance correction: gray world assumption
- Return: dict with keys 'forehead', 'left_cheek', 'right_cheek', 
  each containing [R_mean, G_mean, B_mean]

BUILD signal_processor.py:
- Input: raw RGB time series (T, 3) per ROI, fps=30
- Pipeline:
  Step 1: Linear detrending (scipy.signal.detrend, type='linear')
  Step 2: Moving average subtraction (window=15 frames)
  Step 3: CHROM method rPPG extraction:
    Xs = 3*R - 2*G
    Ys = 1.5*R + G - 1.5*B
    alpha = std(Xs)/std(Ys)
    S = Xs - alpha*Ys
  Step 4: Bandpass filter 0.7-4.0 Hz (scipy.signal.butter order=4, 
    btype='bandpass', then filtfilt for zero phase)
  Step 5: Fuse 3 ROIs: weighted average by SNR of each signal
- Return: clean rPPG signal (T,)

BUILD vitals_estimator.py:
- Input: clean rPPG signal (T,), fps=30
- Heart Rate: FFT → find peak frequency in 0.7-4.0 Hz → multiply by 60
  Use scipy.signal.welch for better frequency resolution (nperseg=256)
  Return HR in BPM with confidence (SNR of peak vs background)
- SpO2: Beer-Lambert approximation
  ratio = std(R_signal) / std(G_signal)  [using red and green channels]
  SpO2 = 110 - 25 * ratio  [empirical formula, calibrate with clip]
  Clamp output: 85-100%
- HRV: 
  Find R peaks using scipy.signal.find_peaks (height=0.3, distance=fps*0.5)
  IBI = diff(peak_indices) / fps * 1000  [milliseconds]
  RMSSD = sqrt(mean(diff(IBI)^2))
  SDNN = std(IBI)
  LF/HF ratio via Lomb-Scargle periodogram (scipy.signal.lombscargle)
- Respiratory Rate:
  Extract respiratory modulation: bandpass filter rPPG at 0.1-0.5 Hz
  Find dominant frequency → multiply by 60
- Return: VitalsResult dataclass with hr, spo2, hrv_rmssd, hrv_sdnn, 
  lf_hf_ratio, rr, confidence_scores dict

BUILD rppg_pipeline.py:
- Main class PRISMrPPGPipeline
- process_video(video_path: str) -> VitalsResult
- process_frame_stream(frames: Iterator) -> VitalsResult  [for real-time]
- Requires minimum 30 seconds of video (900 frames at 30fps)
- If <30 seconds: raise InsufficientDataError
- Log processing time, face detection rate, signal quality
- Unit tests in tests/test_rppg.py:
  Test 1: synthetic sinusoidal signal at known HR → verify estimation ±2 BPM
  Test 2: no face in video → FaceNotDetectedError raised
  Test 3: short video → InsufficientDataError raised

CONFIGS sense_config.yaml:
rppg:
  fps: 30
  min_duration_seconds: 30
  hr_range: [42, 240]
  bandpass_low: 0.7
  bandpass_high: 4.0
  rois: [forehead, left_cheek, right_cheek]

Make all code production-grade: type hints, docstrings, logging (not print), 
proper error handling. Use dataclasses for all return types.
```

---

### PHASE 1.2 — ACOUSTIC BIOMARKER ENGINE

```
Continuing PRISM Layer 1. You have the rPPG engine from Phase 1.1.

TASK: Build the complete acoustic biomarker engine in layer1_sense/audio/

FILES TO CREATE:
layer1_sense/audio/
├── __init__.py
├── cough_detector.py
├── feature_extractor.py
├── cough_classifier.py
├── breathing_analyzer.py
├── voice_biomarker.py
└── audio_pipeline.py

BUILD cough_detector.py:
- Input: audio waveform (numpy), sample_rate=44100
- Step 1: Resample to 22050 Hz (librosa.resample)
- Step 2: Energy-based pre-detection:
  frame_length=1024, hop_length=512
  RMS energy = librosa.feature.rms(y=audio, frame_length=1024, hop_length=512)
  Candidate frames: RMS > 0.15 AND duration > 150ms
- Step 3: Frequency confirmation:
  Compute STFT, check dominant energy in 100-2000 Hz band > 60% of total
- Step 4: CNN binary classifier (cough vs non-cough):
  Architecture: Conv1D(32,3) → ReLU → MaxPool → Conv1D(64,3) → 
  ReLU → MaxPool → Conv1D(128,3) → ReLU → GlobalAvgPool → 
  Dense(64) → Dense(1, sigmoid)
  Input: 22050 samples (1 second), normalized
  Train on: COUGHVID dataset (provide download script)
- Step 5: Segment: 50ms pre-onset + 750ms post-onset per detected cough
- Return: List[CoughSegment] with start_time, end_time, confidence

BUILD feature_extractor.py:
- Input: audio segment (numpy 22050 samples), sample_rate=22050
- Extract ALL of:
  Mel spectrogram: n_mels=128, n_fft=512, hop_length=256, fmax=8000
    → normalize: (mel - mean) / std → shape (128, T)
  MFCC: n_mfcc=40, then delta (order=1), delta-delta (order=2) 
    → concatenate → shape (120, T)
  Chroma STFT: n_chroma=12 → shape (12, T)
  Spectral features (per frame):
    centroid, rolloff(roll_percent=0.85), bandwidth, ZCR, flux
    → shape (5, T)
  Temporal features (scalar):
    duration_ms, peak_amplitude, decay_rate (slope of envelope)
    attack_time (time to peak amplitude)
- Return: AcousticFeatures dataclass with all above as attributes
- Also return: mel_spectrogram_db = librosa.power_to_db(mel, ref=np.max)
  for visualization

BUILD cough_classifier.py:
- Fine-tune YAMNet for 8-class respiratory disease classification
- Classes: {0:TB, 1:COVID, 2:Pneumonia, 3:Whooping_cough, 
            4:Asthma, 5:COPD, 6:Healthy, 7:Uncertain}
- YAMNet loading:
  import tensorflow_hub as hub
  yamnet = hub.load('https://tfhub.dev/google/yamnet/1')
- Custom head:
  class PRISMCoughHead(tf.keras.Model):
    def __init__(self, num_classes=8):
      self.dense1 = Dense(256, activation='relu')
      self.dropout1 = Dropout(0.4)
      self.dense2 = Dense(128, activation='relu')  
      self.dropout2 = Dropout(0.3)
      self.output_layer = Dense(num_classes, activation='softmax')
    def call(self, embeddings):  # embeddings shape (N, 1024)
      x = tf.reduce_mean(embeddings, axis=0, keepdims=True)
      return self.output_layer(self.dropout2(self.dense2(
             self.dropout1(self.dense1(x)))))
- Training function train_cough_classifier(data_dir, epochs=30):
  Phase 1: Freeze YAMNet, train head only — lr=1e-3, 20 epochs
  Phase 2: Unfreeze last 10 layers of YAMNet — lr=1e-4, 10 epochs
  Use class_weight='balanced' (severe class imbalance)
  Augmentation via audiomentations:
    AddGaussianNoise(p=0.5), TimeStretch(p=0.5), 
    PitchShift(min_semitones=-2, max_semitones=2, p=0.4),
    RoomSimulator(p=0.3)
- Also build: 1D CNN ensemble model for complementary features
  Input: raw waveform (22050,) normalized
  Conv1D(64,8,stride=2) → BN → ReLU → Conv1D(128,4,stride=2) → 
  BN → ReLU → Conv1D(256,2) → BN → ReLU → GlobalAvgPool → 
  Dense(128) → Dense(8, softmax)
- Final ensemble: 0.6*yamnet_probs + 0.4*cnn_probs (learned weights)
- predict(audio_segment) -> Dict[disease_name: probability]

BUILD breathing_analyzer.py:
- Input: continuous audio (2+ minutes), sample_rate=22050
- Breath segmentation:
  Compute envelope via Hilbert transform: scipy.signal.hilbert
  Smooth envelope: gaussian filter sigma=500ms
  Find inspiration onset: rising edge above 0.3*max_envelope
  Find expiration onset: falling edge below 0.3*max_envelope
- Breathing features:
  breathing_rate: breaths per minute from inspiration intervals
  ie_ratio: mean(expiration_duration) / mean(inspiration_duration)
  pause_duration: silence between breath cycles
  amplitude_cv: coefficient of variation of breath amplitudes
- Abnormal sound classifiers (separate binary CNNs):
  Wheeze: bandpass 200-800 Hz, detect bi-phasic continuous sounds
    Model: Conv1D(32,16) → MaxPool → Conv1D(64,8) → Dense(1,sigmoid)
  Crackle: detect transient bursts <20ms, broadband frequency content
    Model: same architecture, different training data
  Stridor: bandpass >800 Hz, continuous high-pitched tone
- Severity scoring per abnormality: none/mild/moderate/severe
  Based on: duration %, amplitude, frequency of occurrence

BUILD voice_biomarker.py:
- Input: sustained phonation audio (/aah/ 5 seconds), sample_rate=44100
- Features via parselmouth (praat in Python) — add to requirements:
  pip install praat-parselmouth
  jitter_local: F0 perturbation cycle-to-cycle (normal < 1.04%)
  shimmer_local: amplitude perturbation (normal < 3.81%)
  hnr: harmonics-to-noise ratio (normal > 20 dB)
- Features via pyAudioAnalysis — add to requirements:
  pip install pyAudioAnalysis
  RPDE (recurrence period density entropy)
  DFA (detrended fluctuation analysis)
  PPE (pitch period entropy)
- Classifiers:
  Parkinsons_risk: SVM(kernel='rbf', C=10, gamma='scale') 
    on [jitter, shimmer, hnr, rpde, dfa, ppe, mfcc_mean]
    Train on: UCI Parkinsons dataset (provide download script)
  Dysphonia: binary classifier, same features
  Anemia_risk: correlation model hemoglobin ~ voice_features
    Use CatBoost regressor (pip install catboost)
    Target: hemoglobin estimate ± 1.5 g/dL
- Return: VoiceBiomarkers dataclass with all features + disease scores

BUILD audio_pipeline.py:
- Main class PRISMAudioPipeline
- Methods:
  analyze_cough(audio_path: str) -> CoughAnalysisResult
  analyze_breathing(audio_path: str) -> BreathingAnalysisResult  
  analyze_voice(audio_path: str) -> VoiceBiomarkers
  full_analysis(audio_path: str) -> AudioAnalysisResult
    [runs all three, returns combined]
- full_analysis runs in parallel (concurrent.futures.ThreadPoolExecutor)
- Writes detailed JSON report to output/audio_report_{patient_id}.json
- Unit tests: tests/test_audio.py
  Test 1: pure sine at 440Hz → breathing_rate calculable
  Test 2: COUGHVID sample → classifier returns valid probabilities
  Test 3: silence input → appropriate error/Uncertain class
```

---

### PHASE 1.3 — VISUAL BIOMARKER ENGINE

```
Continuing PRISM Layer 1. You have rPPG and Audio engines.

TASK: Build visual biomarker detection in layer1_sense/visual/

FILES TO CREATE:
layer1_sense/visual/
├── __init__.py
├── face_analyzer.py
├── color_biomarker.py
├── disease_classifier.py
└── visual_pipeline.py

BUILD face_analyzer.py:
- Input: image frame (H,W,3 BGR from OpenCV)
- MediaPipe FaceMesh: get 468 landmarks
- Extract precise anatomical ROIs:
  SCLERA_LEFT: landmark indices [362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398]
  SCLERA_RIGHT: [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246]
  CONJUNCTIVA_LEFT: lower eyelid inner surface landmarks [374,380,381,382,362]
  CONJUNCTIVA_RIGHT: [145,144,163,7,33]
  LIPS: [61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146]
  SKIN_FACE: forehead + cheek region (exclude eyes, lips, eyebrows)
- Convert landmarks to pixel masks: cv2.fillPoly
- Return: FaceROIs dataclass with each region as binary mask + cropped region

BUILD color_biomarker.py:
- Input: image frame + FaceROIs
- Lighting correction per ROI:
  White balance: gray world assumption on full frame
  CLAHE: cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)) on L channel (LAB)
  Skin tone reference: establish baseline from first frame of session
- JAUNDICE detection:
  Analyze sclera ROI in HSV color space
  hue_mean = mean of H channel in sclera region
  saturation_mean = mean of S channel
  Score: jaundice_index = saturation_mean * (hue_mean_normalized_to_yellow)
  Threshold: score > 0.35 → suspect jaundice (bilirubin likely > 2 mg/dL)
  Severity: mild(0.35-0.5), moderate(0.5-0.7), severe(>0.7)
- ANEMIA detection:
  Analyze conjunctiva ROI in RGB
  redness_ratio = R / (R + G + B)  [per pixel mean]
  pallor_score = 1 - redness_ratio  (normalized)
  Threshold: redness_ratio < 0.42 → suspect anemia (Hb likely < 10 g/dL)
  Correlate with rPPG-based SpO2 for cross-validation
- CYANOSIS detection:
  Analyze lips ROI
  blue_dominance = B / (R + G + B)
  cyanosis_score = blue_dominance - expected_baseline
  Threshold: blue_dominance > 0.38 → cyanosis (SpO2 likely < 94%)
- DENGUE FLUSH:
  Full face skin analysis
  Detect periorbital redness: elevated R channel around eye region
  Flush_score = R_face / baseline_R
  Pattern: diffuse redness + periorbital concentration → dengue flush pattern
- PALLOR:
  Overall luminance of face skin vs stored population mean (by skin tone tier)
  pallor_percentage = (baseline_luminance - current_luminance) / baseline_luminance
- Return: ColorBiomarkers with scores + severity for each condition

BUILD disease_classifier.py:
- Multi-task MobileNetV3-Large fine-tuned model
- Architecture:
  backbone = torchvision.models.mobilenet_v3_large(pretrained=True)
  Replace final classifier with 4 parallel heads:
  class PRISMVisualClassifier(nn.Module):
    def __init__(self):
      self.backbone = mobilenet_v3_large features (all layers)
      self.pool = nn.AdaptiveAvgPool2d(1)
      hidden = 512
      # 4 task heads
      self.jaundice_head = nn.Sequential(
        nn.Linear(960, hidden), nn.ReLU(), nn.Dropout(0.4), 
        nn.Linear(hidden, 4))  # 0:none,1:mild,2:moderate,3:severe
      self.anemia_head = nn.Sequential(
        nn.Linear(960, hidden), nn.ReLU(), nn.Dropout(0.4),
        nn.Linear(hidden, 2))  # binary
      self.cyanosis_head = nn.Sequential(
        nn.Linear(960, hidden), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(hidden, 2))
      self.dengue_head = nn.Sequential(
        nn.Linear(960, hidden), nn.ReLU(), nn.Dropout(0.3),
        nn.Linear(hidden, 2))
  Training data:
    Jaundice: ISIC + custom web-scraped scleral jaundice images (500+)
    Anemia: EyePACS conjunctival pallor subset
    Download scripts in scripts/download_visual_data.py
  Loss: sum of CrossEntropy for all 4 heads (multi-task)
  Regularization: L2 + label smoothing 0.1
- Training:
  Phase 1: Freeze backbone, train heads — lr=1e-3, 15 epochs
  Phase 2: Unfreeze last 5 backbone layers — lr=5e-5, 10 epochs
  Data augmentation: RandomHorizontalFlip, ColorJitter(0.2,0.2,0.2,0.1),
    RandomRotation(10), RandomResizedCrop(224, scale=(0.8,1.0))
- predict(face_image_224x224) -> VisualDiseaseScores

BUILD visual_pipeline.py:
- Main class PRISMVisualPipeline
- analyze_frame(frame: np.ndarray) -> VisualBiomarkerResult
- analyze_video(video_path: str, fps: int = 30) -> VisualBiomarkerResult
  [aggregate predictions over multiple frames, take median for stability]
- Cross-validate color_biomarker scores against classifier outputs
  If color_biomarker says jaundice but classifier says no: flag as uncertain
- Return: VisualBiomarkerResult with all scores + uncertainty flags
```

---

### PHASE 1.4 — CROSS-MODAL ATTENTION FUSION

```
Continuing PRISM Layer 1. You have all 4 signal modules.

TASK: Build the cross-modal attention fusion model that combines
rPPG + Audio + Visual + IMU signals into unified disease predictions.

FILE: layer1_sense/fusion/cross_modal_fusion.py

ARCHITECTURE (implement exactly):

class PRISMFusionModel(nn.Module):
    """
    Cross-Modal Attention Fusion for multimodal medical diagnosis.
    Fuses: audio embeddings, visual embeddings, rPPG embeddings, IMU embeddings
    """
    EMBED_DIM = 128
    NUM_HEADS = 4
    NUM_DISEASES = 12  
    # [TB, Pneumonia, COVID, Asthma, COPD, Anemia, Jaundice, 
    #  Dengue, HeartFailure, Parkinsons, Depression, Cardiac_Risk]
    
    def __init__(self):
        # Modality encoders (each maps to 128-dim)
        self.audio_encoder = nn.Sequential(
            nn.Linear(8, 64), nn.ReLU(),  # 8 cough disease probs
            nn.Linear(64, 128), nn.LayerNorm(128)
        )
        self.visual_encoder = nn.Sequential(
            nn.Linear(12, 64), nn.ReLU(),  # visual biomarker scores
            nn.Linear(64, 128), nn.LayerNorm(128)
        )
        self.rppg_encoder = nn.Sequential(
            nn.Linear(6, 64), nn.ReLU(),  # HR, SpO2, HRV, LF/HF, RR, confidence
            nn.Linear(64, 128), nn.LayerNorm(128)
        )
        self.imu_encoder = nn.Sequential(
            nn.Linear(5, 32), nn.ReLU(),  # gait features
            nn.Linear(32, 128), nn.LayerNorm(128)
        )
        
        # Positional encoding (each modality gets unique learned position)
        self.modality_embeddings = nn.Embedding(4, 128)
        
        # Cross-modal multi-head attention
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=128, num_heads=4, dropout=0.1, batch_first=True
        )
        
        # Feed-forward after attention
        self.ffn = nn.Sequential(
            nn.Linear(128, 256), nn.GELU(),
            nn.Dropout(0.1), nn.Linear(256, 128)
        )
        self.norm1 = nn.LayerNorm(128)
        self.norm2 = nn.LayerNorm(128)
        
        # Final disease classifier
        self.classifier = nn.Sequential(
            nn.Linear(512, 256), nn.GELU(), nn.Dropout(0.3),
            nn.Linear(256, 128), nn.GELU(), nn.Dropout(0.2),
            nn.Linear(128, self.NUM_DISEASES)
            # No softmax — use sigmoid for multi-label
        )
        
        # Modality availability mask (handle missing modalities)
        # e.g., if IMU not available, mask it out

    def forward(self, audio_feats, visual_feats, rppg_feats, 
                imu_feats=None, modality_mask=None):
        # Encode each modality
        a = self.audio_encoder(audio_feats).unsqueeze(1)   # (B,1,128)
        v = self.visual_encoder(visual_feats).unsqueeze(1) # (B,1,128)
        r = self.rppg_encoder(rppg_feats).unsqueeze(1)     # (B,1,128)
        
        if imu_feats is not None:
            i = self.imu_encoder(imu_feats).unsqueeze(1)   # (B,1,128)
            modalities = torch.cat([a, v, r, i], dim=1)    # (B,4,128)
        else:
            modalities = torch.cat([a, v, r], dim=1)       # (B,3,128)
        
        # Add modality position encodings
        positions = torch.arange(modalities.size(1), device=modalities.device)
        modalities = modalities + self.modality_embeddings(positions)
        
        # Cross-modal attention (each modality attends to all others)
        attn_out, attn_weights = self.cross_attention(
            modalities, modalities, modalities,
            key_padding_mask=modality_mask
        )
        # Add & Norm
        modalities = self.norm1(modalities + attn_out)
        ffn_out = self.ffn(modalities)
        modalities = self.norm2(modalities + ffn_out)
        
        # Flatten all modality embeddings
        fused = modalities.reshape(modalities.size(0), -1)  # (B, 4*128)
        
        # Predict diseases
        logits = self.classifier(fused)
        probabilities = torch.sigmoid(logits)  # multi-label
        
        return probabilities, attn_weights  # return attention for explainability

ALSO BUILD:
- fusion_trainer.py: training loop with synthetic data + MIMIC features
- Missing modality handling: if audio fails → zero-fill + mask
- Uncertainty: MC Dropout (T=20 forward passes) for epistemic uncertainty
  std across passes = uncertainty estimate
- Calibration: temperature scaling after training
- Export to ONNX: fusion_model.onnx for edge deployment

EVALUATION:
- Synthetic test: feed known-pattern inputs, verify attention weights 
  focus on relevant modalities
- Ablation: run with 1,2,3,4 modalities → verify fusion > any single modality
```

---

### PHASE 1.5 — TFLITE EXPORT + ANDROID INTEGRATION

```
Continuing PRISM Layer 1. All signal models are built.

TASK: Export all models to TFLite for on-device Android inference.
Create the Android integration module specs.

BUILD scripts/export_to_tflite.py:

EXPORT PIPELINE for each model:

1. YAMNet cough classifier:
   - Save as SavedModel: model.save('saved_models/cough_classifier')
   - Convert with FP16 quantization:
     converter = tf.lite.TFLiteConverter.from_saved_model('saved_models/cough_classifier')
     converter.optimizations = [tf.lite.Optimize.DEFAULT]
     converter.target_spec.supported_types = [tf.float16]
     tflite_model = converter.convert()
     open('tflite_models/cough_classifier.tflite', 'wb').write(tflite_model)
   - Verify: run TFLite interpreter on test sample, compare with original

2. rPPG signal processor:
   - Export signal processing (filtering, peak detection) as TFLite ops
   - Use tf.signal for FFT operations (TFLite compatible)
   - Model: takes (900, 3) raw RGB time series → outputs (hr, spo2, hrv, rr)

3. Visual biomarker classifier (MobileNetV3):
   - PyTorch → ONNX → TFLite via onnx-tf:
     torch.onnx.export(model, dummy, 'visual_classifier.onnx', opset_version=12)
     onnx_tf.backend.prepare(onnx_model).export_graph('visual_classifier_tf')
     [then TFLite converter as above]

4. Fusion model:
   - Smallest model — quantize to INT8 for fastest inference:
     converter.optimizations = [tf.lite.Optimize.DEFAULT]
     converter.representative_dataset = representative_data_gen
     converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
     converter.inference_input_type = tf.int8
     converter.inference_output_type = tf.float32

BENCHMARK SCRIPT (scripts/benchmark_tflite.py):
- Load each TFLite model
- Run 100 inference calls
- Report: mean latency (ms), p95 latency (ms), model size (MB), accuracy vs original
- Target: cough classifier < 50ms, rPPG < 100ms, visual < 30ms, fusion < 10ms

BUILD Android Integration Spec (android_integration/README.md):
- Document exact method signatures for Android team (Person 4):
  PRISMSenseModule.initialize(context: Context, modelDir: String)
  PRISMSenseModule.analyzeVideo(videoPath: String): SenseResult
  PRISMSenseModule.analyzeAudio(audioPath: String): AudioResult
  PRISMSenseModule.analyzeRealtime(cameraFrames: Flow<Bitmap>): Flow<PartialResult>
- Specify: model file names, input shapes, output tensor indices
- Include: example Kotlin/Java code snippets for each method

FINAL INTEGRATION TEST:
- End-to-end test: dummy patient data → all 4 pipelines → fusion → disease probs
- Assert: output shape (12,) probabilities, all in [0,1], sum not forced to 1
- Performance: full pipeline < 500ms on laptop (proxy for mid-range Android)
```

---
---

# PERSON 2: CAUSAL AI ENGINEER
## Layer 2 — REASON (Causal Discovery + SCM + Counterfactuals)

---

### PHASE 2.1 — DATA PIPELINE + MIMIC-IV PREPROCESSING

```
You are building PRISM, a production-grade multimodal medical diagnostic platform.
You are Person 2 — Causal AI Engineer responsible for Layer 2: REASON.

TASK: Build the complete data preprocessing pipeline for MIMIC-IV and 
NFHS-5 data that feeds the causal engine.

PROJECT STRUCTURE:
prism/
├── layer2_reason/
│   ├── __init__.py
│   ├── data/
│   │   ├── mimic_preprocessor.py
│   │   ├── nfhs_preprocessor.py
│   │   ├── data_validator.py
│   │   └── feature_engineering.py
│   ├── causal_discovery/
│   ├── scm/
│   ├── counterfactuals/
│   └── tests/

REQUIREMENTS (add to requirements.txt):
dowhy==0.11.1
causalml==0.15.0
tigramite==5.2.1.0
dice-ml==0.9
shap==0.44.1
pgmpy==0.1.25
causal-learn==0.1.3.8
econml==0.15.1
networkx==3.2.1

BUILD mimic_preprocessor.py:
- Assumes MIMIC-IV CSV files in data/raw/mimic_iv/
- Target: extract patient biomarker time series for causal analysis
- Tables needed: admissions, patients, labevents, chartevents, diagnoses_icd
- Extract time series per patient for these variables (itemids provided):
  hemoglobin: ITEMID 51222
  wbc: ITEMID 51301  
  creatinine: ITEMID 50912
  temperature: ITEMID 223762
  heart_rate: ITEMID 220045
  spo2: ITEMID 220277
  respiratory_rate: ITEMID 220210
  sbp: ITEMID 220179
  glucose: ITEMID 220621
  crp: ITEMID 50889
  bilirubin_total: ITEMID 50885
  platelet: ITEMID 51265
- Label extraction from diagnoses_icd:
  TB: ICD10 starts with 'A15','A16','A17','A18','A19'
  Pneumonia: 'J12','J13','J14','J15','J16','J17','J18'
  Sepsis: 'A40','A41'
  Heart failure: 'I50'
  Anemia: 'D50','D51','D52','D53','D64'
  Dengue: 'A90','A91'
- Output format per patient:
  {patient_id: str, 
   timeseries: pd.DataFrame(columns=[time_hours, *biomarkers]),
   labels: List[str],  # ICD10 labels
   demographics: {age, sex, admission_weight, bmi}}
- Handle missing values:
  Linear interpolation for gaps < 4 hours
  Forward fill for gaps 4-12 hours
  Leave NaN for gaps > 12 hours (tigramite handles missing)
- Filter: minimum 48 hours of data, minimum 5 distinct biomarker readings
- Output: save to data/processed/mimic_patients.pkl (list of patient dicts)
- Log: n_patients, n_per_disease, missing_rate_per_biomarker

BUILD nfhs_preprocessor.py:
- NFHS-5 data (download from dhsprogram.com/data)
- Extract India-specific features:
  nutrition: hv237 (food security), hml32 (malnutrition z-scores)
  anemia: hb56 (hemoglobin), hb57 (anemia level)
  tb_symptoms: s103a-s103e (cough, fever, weight loss flags)
  socioeconomic: hv270 (wealth index), hv025 (urban/rural)
  water_sanitation: hv201, hv205 (water source, toilet type)
  crowding: hv216 (rooms), hv009 (household members)
- Compute derived features:
  crowding_index = hv009 / hv216
  anemia_binary = 1 if hemoglobin < 11 (children) or < 12 (women)
  tb_symptom_score = sum of s103a through s103e
- Output: pd.DataFrame saved to data/processed/nfhs_india.pkl

BUILD feature_engineering.py:
- Input: preprocessed patient timeseries
- Compute lagged features for causal analysis:
  For each biomarker X at time t, create:
    X_lag1 = X(t - 6h), X_lag2 = X(t - 12h),..., X_lag20 = X(t - 5days)
  Also: first_difference = X(t) - X(t-1)
  Also: rolling_mean_24h, rolling_std_24h, rolling_max_24h
- Normalize: StandardScaler per biomarker (save scaler for inference)
- Create panel dataset: (n_patients × n_timepoints, n_features)
- Output: data/processed/panel_dataset.pkl + scalers/biomarker_scalers.pkl
```

---

### PHASE 2.2 — CAUSAL DISCOVERY ENGINE

```
Continuing PRISM Layer 2. You have preprocessed MIMIC-IV and NFHS data.

TASK: Build causal discovery using PCMCI (temporal) and FCI (with 
latent confounders) to learn causal graphs from patient data.

FILES TO CREATE:
layer2_reason/causal_discovery/
├── __init__.py
├── pcmci_discoverer.py
├── fci_discoverer.py
├── graph_validator.py
├── causal_graph_store.py
└── discovery_pipeline.py

BUILD pcmci_discoverer.py:
- Uses tigramite library
- Input: panel_dataset (n_patients × T, n_biomarkers) as pd.DataFrame
- PCMCI configuration:
  from tigramite.pcmci import PCMCI
  from tigramite.independence_tests import ParCorr, CMIknn
  from tigramite import data_processing as pp
  
  dataframe = pp.DataFrame(
      data=timeseries_array,       # shape (T, N_vars)
      datatime=time_array,
      var_names=biomarker_names,
      missing_flag=np.nan
  )
  
  parcorr = ParCorr(significance='analytic')
  pcmci = PCMCI(dataframe=dataframe, cond_ind_test=parcorr, verbosity=1)
  
  results = pcmci.run_pcmci(
      tau_min=1,           # minimum lag: 6 hours (if hourly data)
      tau_max=20,          # maximum lag: 5 days
      pc_alpha=0.05,       # significance threshold for PC step
  )
  
  # Run MCI test for accurate p-values
  results_mci = pcmci.run_mci(
      selected_links=results['p_matrix'] < 0.05,
      tau_min=1, tau_max=20
  )
  
- Significant links: p_value < 0.05 AND |effect_size| > 0.1
- Extract causal graph as networkx DiGraph:
  nodes = biomarker names
  edges = (cause, effect, lag_hours) where significant
  edge_weight = MCI partial correlation coefficient
  
- Separate analysis per disease cohort:
  Run PCMCI on TB patients only → TB_causal_graph
  Run PCMCI on Anemia patients → Anemia_causal_graph
  Run on full population → general_causal_graph
  
- Output: 
  graphs/pcmci_tb_graph.pkl
  graphs/pcmci_anemia_graph.pkl  
  graphs/pcmci_general_graph.pkl
  
- Visualization: tigramite plot_graph() → save to figures/

BUILD fci_discoverer.py:
- Uses causal-learn library (handles latent confounders)
- Input: cross-sectional NFHS data (no time series needed)
- FCI setup:
  from causallearn.search.ConstraintBased.FCI import fci
  from causallearn.utils.cit import fisherz
  
  # FCI with Fisher-Z conditional independence test
  G, edges = fci(
      dataset=nfhs_array,          # (n_patients, n_features)
      independence_test_method=fisherz,
      alpha=0.05,
      depth=-1,                    # unlimited depth
      max_path_length=4,
      verbose=True
  )
  
- Parse output PAG (Partial Ancestral Graph):
  Arrow types: → (direct cause), ↔ (bidirected = latent common cause),
               o→ (possible direct cause)
  Convert to networkx with edge type attributes
  
- Domain knowledge constraints (encode as background knowledge):
  Malnutrition → TB_susceptibility (must exist, not reversible)
  Age → Hemoglobin (must exist)
  Use FCI background knowledge parameter:
  from causallearn.utils.BackgroundKnowledge import BackgroundKnowledge
  bk = BackgroundKnowledge()
  bk.add_required_by_node(malnutrition_idx, tb_idx)

BUILD graph_validator.py:
- Validate discovered graphs against known medical knowledge
- Checks:
  1. Acyclicity: networkx.is_directed_acyclic_graph(G) — warn if false
  2. Known edges present: check required_edges list against graph
     required_edges = [(malnutrition, tb), (low_hb, fatigue), 
                       (high_wbc, infection), (fever, infection)]
  3. Impossible edges absent: check forbidden_edges list
     forbidden_edges = [(tb, malnutrition)]  # TB doesn't cause malnutrition
  4. Connectivity: all disease nodes reachable from at least 2 biomarkers
- Report: validation_report.json with pass/fail per check + human explanation
- Merge PC and FCI graphs: use union where confident, mark uncertain edges

BUILD causal_graph_store.py:
- Stores causal graphs as JSON (serializable networkx)
- disease_graphs: Dict[disease_name, nx.DiGraph]
- Methods:
  save_graph(disease, graph)
  load_graph(disease) -> nx.DiGraph
  get_parents(disease, node) -> List[node]
  get_causal_path(source, target) -> List[path]
  export_dot(disease) -> str  [Graphviz DOT format for visualization]
```

---

### PHASE 2.3 — STRUCTURAL CAUSAL MODEL + DO-CALCULUS

```
Continuing PRISM Layer 2. You have validated causal graphs.

TASK: Build Structural Causal Models and implement do-calculus 
for intervention analysis.

FILES TO CREATE:
layer2_reason/scm/
├── __init__.py
├── scm_builder.py
├── intervention_engine.py
├── causal_attribution.py
└── scm_pipeline.py

BUILD scm_builder.py:
- Build full SCM from causal graph
- For each node X_i: fit X_i = f_i(PA_i) + noise_i
  where PA_i = causal parents from graph
- Functional forms:
  Option A: Linear SCM (fast, interpretable):
    from sklearn.linear_model import LinearRegression
    model_i = LinearRegression().fit(parent_features, X_i_values)
  Option B: Nonlinear SCM (accurate):
    from sklearn.ensemble import GradientBoostingRegressor
    model_i = GradientBoostingRegressor(n_estimators=100).fit(PA_i, X_i)
  Use Option B for production, Option A for debugging
- Noise estimation:
  residuals_i = X_i - f_i(PA_i)
  noise_i ~ N(mean(residuals_i), std(residuals_i))
- Fit SCMs separately per disease cohort
- Store: Dict[node_name, (fitted_model, noise_params)]
- Save: scm_models/tb_scm.pkl, anemia_scm.pkl, etc.

BUILD intervention_engine.py:
- Implements Pearl's do-calculus
- Uses DoWhy library on top of fitted SCMs:
  import dowhy
  from dowhy import CausalModel
  
  def estimate_intervention_effect(
      patient_data: pd.Series,
      treatment_var: str,
      treatment_value: float,
      outcome_var: str,
      disease: str
  ) -> InterventionResult:
  
    # Build DoWhy model from our causal graph
    model = CausalModel(
        data=disease_cohort_df,
        graph=causal_graph_as_dot[disease],
        treatment=treatment_var,
        outcome=outcome_var
    )
    
    # Identify causal effect (automatic adjustment set selection)
    identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
    
    # Estimate with backdoor linear regression
    estimate = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.linear_regression",
        target_units="ate"
    )
    
    # Refutation tests (verify estimate is real, not spurious)
    refutation = model.refute_estimate(
        identified_estimand, estimate,
        method_name="random_common_cause"  # Add random variable, effect should stay
    )
    
    return InterventionResult(
        baseline_outcome=patient_data[outcome_var],
        intervened_outcome=estimate.value,
        absolute_reduction=patient_data[outcome_var] - estimate.value,
        relative_reduction_pct=(patient_data[outcome_var] - estimate.value) / 
                                 patient_data[outcome_var] * 100,
        p_value_refutation=refutation.new_effect,
        confidence_interval=estimate.get_confidence_intervals()
    )

- Key interventions to pre-compute:
  TB: do(nutrition_score=adequate), do(ventilation=improved), do(bmi=normal)
  Anemia: do(iron_supplementation=yes), do(diet_diversity=high)
  Heart: do(smoking=quit), do(activity=moderate), do(diet=heart_healthy)
  Dengue: do(vector_control=yes), do(hydration=adequate)

BUILD causal_attribution.py:
- Decompose disease probability into causal factor contributions
- Implementation using DoWhy + custom CausalSHAP:
  
  def compute_causal_attribution(patient_data, disease):
    # For each potential cause C of disease D:
    causes = causal_graph.predecessors(disease)
    attributions = {}
    
    for cause in causes:
      # Intervene: set cause to population baseline
      counterfactual_prob = intervention_engine.estimate(
          patient_data, 
          treatment=cause, 
          treatment_value=population_baseline[cause],
          outcome=f"{disease}_probability"
      )
      # Attribution = how much does prob change when cause is "fixed"
      attributions[cause] = patient_data[f"{disease}_probability"] - counterfactual_prob
    
    # Normalize to sum to 1 (relative contributions)
    total = sum(abs(v) for v in attributions.values())
    return {k: v/total for k,v in attributions.items()}
  
  # Output: {"malnutrition": 0.38, "poor_ventilation": 0.24, 
  #           "prior_infection": 0.21, "genetics_proxy": 0.17}

BUILD scm_pipeline.py:
- Main class PRISMCausalEngine
- Methods:
  analyze_patient(patient_features: Dict, disease: str) -> CausalAnalysisResult
    Returns:
      - disease_probability (from Layer 1, passed in)
      - causal_attributions: Dict[cause, weight]
      - top_3_counterfactuals: List[CounterfactualResult]
        each with: intervention, baseline_prob, intervened_prob, feasibility_score
      - recommended_intervention: the single highest-impact feasible action
  
  batch_analyze(patient_cohort: List[Dict]) -> List[CausalAnalysisResult]
    [parallel processing with ThreadPoolExecutor]
  
- Response time target: < 200ms per patient (pre-compute graphs at startup)
- Cache: LRU cache for repeated similar patient profiles (functools.lru_cache)
```

---

### PHASE 2.4 — COUNTERFACTUALS + CAUSAL VAE

```
Continuing PRISM Layer 2. SCM engine is built.

TASK: Build DiCE counterfactual generation and the Causal VAE 
for learned causal representations.

FILES TO CREATE:
layer2_reason/counterfactuals/
├── __init__.py
├── dice_generator.py
├── causal_vae.py
├── counterfactual_ranker.py
└── explainer.py

BUILD dice_generator.py:
- Uses DiCE-ML for diverse, actionable counterfactuals
- Implementation:
  import dice_ml
  from dice_ml import Dice
  
  def generate_counterfactuals(
      patient: pd.Series,
      disease_model,        # sklearn/torch model
      n_counterfactuals=5,
      actionable_features=['nutrition_score', 'bmi', 'activity_level',
                           'smoking_status', 'water_quality', 'crowding_index']
  ) -> List[CounterfactualExplanation]:
  
    d = dice_ml.Data(
        dataframe=reference_cohort_df,
        continuous_features=['nutrition_score', 'bmi', 'activity_level', 
                             'crowding_index', 'hemoglobin'],
        outcome_name='disease_label'
    )
    
    m = dice_ml.Model(model=disease_model, backend="sklearn")
    exp = Dice(d, m, method="genetic")  # genetic = diverse counterfactuals
    
    cf = exp.generate_counterfactuals(
        query_instances=patient.to_frame().T,
        total_CFs=n_counterfactuals,
        desired_class="healthy",
        proximity_weight=1.5,     # prefer small changes
        diversity_weight=1.0,     # ensure diverse options
        features_to_vary=actionable_features
    )
    
    return parse_dice_output(cf)

  def parse_dice_output(cf_obj) -> List[CounterfactualExplanation]:
    results = []
    for cf in cf_obj.cf_examples_list[0].final_cfs_df.iterrows():
      changes = {feat: (patient[feat], cf[feat]) 
                 for feat in actionable_features if patient[feat] != cf[feat]}
      results.append(CounterfactualExplanation(
          changes=changes,
          new_disease_probability=cf['disease_label'],
          n_features_changed=len(changes),
          feasibility_score=compute_feasibility(changes)
      ))
    return sorted(results, key=lambda x: x.feasibility_score, reverse=True)
  
  def compute_feasibility(changes: Dict) -> float:
    # Score based on ease of implementation
    feasibility_weights = {
        'nutrition_score': 0.9,    # Easy: ICDS scheme
        'activity_level': 0.8,     # Moderate: lifestyle
        'smoking_status': 0.5,     # Hard: addiction
        'crowding_index': 0.2,     # Very hard: housing
        'water_quality': 0.6,      # Moderate: govt schemes
        'bmi': 0.7                 # Moderate: nutrition
    }
    return np.mean([feasibility_weights.get(f, 0.5) for f in changes.keys()])

BUILD causal_vae.py:
- Causal VAE: learns disentangled causal latent factors
- Architecture (PyTorch):
  
  class CausalVAE(nn.Module):
    """
    Variational Autoencoder with causal structure in latent space.
    Latent variables follow a DAG structure (not independent).
    Reference: CausalVAE (Yang et al., 2021)
    """
    def __init__(self, input_dim=15, latent_dim=8, hidden_dim=128):
      # Encoder: x → (mu, log_var) for each latent factor
      self.encoder = nn.Sequential(
          nn.Linear(input_dim, hidden_dim), nn.ReLU(),
          nn.Linear(hidden_dim, hidden_dim), nn.ReLU()
      )
      self.mu_nets = nn.ModuleList([nn.Linear(hidden_dim, 1) 
                                    for _ in range(latent_dim)])
      self.logvar_nets = nn.ModuleList([nn.Linear(hidden_dim, 1) 
                                        for _ in range(latent_dim)])
      
      # Causal mask: learned adjacency matrix for latent DAG
      # Initialize with domain knowledge (triangular = DAG structure)
      self.causal_mask = nn.Parameter(
          torch.tril(torch.ones(latent_dim, latent_dim), diagonal=-1)
      )
      
      # Structural equations in latent space: z_i = f_i(z_{PA_i}) + eps_i
      self.structural_eqs = nn.ModuleList([
          nn.Linear(latent_dim, 1) for _ in range(latent_dim)
      ])
      
      # Decoder: z → x_recon
      self.decoder = nn.Sequential(
          nn.Linear(latent_dim, hidden_dim), nn.ReLU(),
          nn.Linear(hidden_dim, hidden_dim), nn.ReLU(),
          nn.Linear(hidden_dim, input_dim)
      )
    
    def encode(self, x):
      h = self.encoder(x)
      mus = [net(h) for net in self.mu_nets]
      logvars = [net(h) for net in self.logvar_nets]
      return torch.cat(mus, dim=1), torch.cat(logvars, dim=1)
    
    def reparameterize(self, mu, logvar):
      std = torch.exp(0.5 * logvar)
      return mu + std * torch.randn_like(std)
    
    def causal_forward(self, z_ind):
      # Apply causal structure: z_causal = (I - A^T)^{-1} z_ind
      # where A is the learned causal adjacency
      A = torch.sigmoid(self.causal_mask) * torch.tril(
          torch.ones_like(self.causal_mask), diagonal=-1)
      I = torch.eye(A.size(0), device=A.device)
      z_causal = torch.linalg.solve(I - A.T, z_ind.T).T
      return z_causal
    
    def do_intervention(self, x, intervention_dict):
      # do(z_i = val): set specific latent factor, propagate downstream
      mu, logvar = self.encode(x)
      z = self.reparameterize(mu, logvar)
      z_causal = self.causal_forward(z)
      # Apply intervention
      for idx, val in intervention_dict.items():
          z_causal[:, idx] = val
      return self.decoder(z_causal)
    
    def forward(self, x):
      mu, logvar = self.encode(x)
      z = self.reparameterize(mu, logvar)
      z_causal = self.causal_forward(z)
      x_recon = self.decoder(z_causal)
      return x_recon, mu, logvar, z_causal
  
  # Loss function:
  def causal_vae_loss(x_recon, x, mu, logvar, z_causal, beta=4.0, lambda_dag=1.0):
    recon_loss = F.mse_loss(x_recon, x, reduction='sum')
    kl_loss = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    # DAG constraint: h(A) = tr(e^{A circ A}) - d = 0 (NOTEARS)
    A = torch.sigmoid(causal_mask)
    dag_loss = lambda_dag * (torch.trace(torch.matrix_exp(A * A)) - A.size(0))
    return recon_loss + beta * kl_loss + dag_loss
```

---

### PHASE 2.5 — FULL CAUSAL PIPELINE INTEGRATION + TESTS

```
Continuing PRISM Layer 2. All causal components are built.

TASK: Integrate all causal components into unified PRISMCausalEngine 
and write comprehensive tests.

BUILD layer2_reason/causal_engine.py (main integration class):

class PRISMCausalEngine:
  def __init__(self, disease: str, graphs_dir: str, models_dir: str):
    self.disease = disease
    self.causal_graph = CausalGraphStore.load_graph(disease)
    self.scm = SCMPipeline.load(models_dir, disease)
    self.dice_gen = DiCEGenerator(reference_data_path=...)
    self.causal_vae = CausalVAE.load(models_dir)
  
  def full_causal_analysis(
      self,
      patient_features: Dict[str, float],
      disease_probability: float,  # from Layer 1
      top_k_counterfactuals: int = 3
  ) -> CausalReport:
    
    # 1. Causal attribution (WHY does this patient have this disease?)
    attributions = causal_attribution.compute(patient_features, self.disease)
    
    # 2. Top interventions (what changes the outcome most?)
    interventions = []
    for actionable_cause in self.get_actionable_causes():
      effect = intervention_engine.estimate_effect(
          patient_features, actionable_cause, self.disease)
      interventions.append(effect)
    interventions.sort(key=lambda x: x.absolute_reduction, reverse=True)
    
    # 3. Diverse counterfactuals
    counterfactuals = self.dice_gen.generate(
        patient_features, n=top_k_counterfactuals)
    
    # 4. Narrative explanation (structured, not LLM-generated)
    narrative = self.build_narrative(
        disease_probability, attributions, interventions[:3])
    
    return CausalReport(
        disease=self.disease,
        probability=disease_probability,
        causal_attributions=attributions,  # sorted by impact
        top_interventions=interventions[:3],
        counterfactuals=counterfactuals,
        narrative=narrative,
        causal_graph_dot=causal_graph_store.export_dot(self.disease)
    )
  
  def build_narrative(self, prob, attributions, interventions) -> str:
    # Template-based narrative (not LLM — deterministic, auditable)
    top_cause = max(attributions, key=attributions.get)
    top_intervention = interventions[0]
    return (
      f"{self.disease} probability: {prob:.0%}. "
      f"Primary driver: {top_cause} ({attributions[top_cause]:.0%} contribution). "
      f"Highest-impact intervention: {top_intervention.treatment} "
      f"reduces probability by {top_intervention.relative_reduction_pct:.0f}% "
      f"(from {prob:.0%} to {prob - top_intervention.absolute_reduction:.0%})."
    )

TESTS (layer2_reason/tests/test_causal_engine.py):
Test 1: Known causal structure
  - Create synthetic data from known SCM
  - Run PCMCI → verify all known edges recovered (recall > 0.8)
  - Assert: no impossible edges present

Test 2: Intervention correctness  
  - Patient with known high-malnutrition, high TB probability
  - do(malnutrition=0) → verify TB probability decreases
  - Assert: decreased, not increased or unchanged

Test 3: Counterfactual validity
  - Generate counterfactual → apply to model → verify disease class changes
  - Assert: n_features_changed is minimal (proximity constraint)

Test 4: Narrative determinism
  - Same input → same narrative (no randomness)
  - Different inputs → different narratives

Test 5: Performance
  - full_causal_analysis on 100 patients
  - Assert: mean time < 200ms per patient
```

---
---

# PERSON 3: DEEP LEARNING ENGINEER
## Layer 3+4 — Neural ODE Digital Twin + RL Intervention Optimizer

---

### PHASE 3.1 — LATENT ODE FOUNDATION

```
You are building PRISM. You are Person 3 — Deep Learning Engineer.
Responsible for Layer 3 (Digital Twin) and Layer 4 (RL Optimizer).

TASK: Implement the Latent ODE architecture for patient trajectory modeling.

PROJECT STRUCTURE:
prism/
├── layer3_twin/
│   ├── __init__.py
│   ├── latent_ode/
│   │   ├── __init__.py
│   │   ├── ode_func.py
│   │   ├── encoder.py
│   │   ├── latent_ode_model.py
│   │   ├── solver.py
│   │   └── trainer.py
│   ├── organ_twins/
│   └── causal_integration/
├── layer4_rl/
└── tests/

REQUIREMENTS (add):
torchdiffeq==0.2.3
torchsde==0.2.6
pytorch-lightning==2.1.3
wandb==0.16.6
einops==0.7.0

BUILD ode_func.py:
- Neural network defining dx/dt = f_theta(x, t)
- Multiple architectures to try:

  class ODEFunc(nn.Module):
    """Base ODE function — defines dynamics"""
    def __init__(self, latent_dim=32, hidden_dim=64, depth=3):
      layers = []
      layers.append(nn.Linear(latent_dim + 1, hidden_dim))  # +1 for time
      layers.append(nn.Tanh())
      for _ in range(depth - 2):
        layers.append(nn.Linear(hidden_dim, hidden_dim))
        layers.append(nn.Tanh())  # Tanh better than ReLU for ODEs (smoother)
      layers.append(nn.Linear(hidden_dim, latent_dim))
      self.net = nn.Sequential(*layers)
      
      # Initialize near-zero for stability (small perturbation dynamics)
      for m in self.net.modules():
        if isinstance(m, nn.Linear):
          nn.init.normal_(m.weight, mean=0, std=0.01)
          nn.init.zeros_(m.bias)
    
    def forward(self, t, x):
      # Augment with time for non-autonomous dynamics
      t_vec = t.expand(x.size(0), 1) if x.dim() > 1 else t.unsqueeze(0)
      return self.net(torch.cat([x, t_vec], dim=-1))
  
  class AugmentedODEFunc(ODEFunc):
    """Augmented Neural ODE — adds augmentation dimensions for expressivity"""
    def __init__(self, latent_dim, aug_dim=5, **kwargs):
      super().__init__(latent_dim + aug_dim, **kwargs)
      self.aug_dim = aug_dim
    
    def forward(self, t, x):
      # x already includes augmentation dimensions
      return super().forward(t, x)

BUILD encoder.py:
- ODE-RNN Encoder: handles irregular time series → latent state z0

  class ODERNNEncoder(nn.Module):
    """
    Encodes irregular patient observations into initial latent state z0.
    Processes observations in reverse chronological order.
    Between observations: evolve hidden state with ODE.
    At each observation: update with GRU.
    """
    def __init__(self, input_dim, latent_dim=32, hidden_dim=64):
      self.latent_dim = latent_dim
      self.ode_func = ODEFunc(latent_dim, hidden_dim)
      self.gru_cell = nn.GRUCell(
          input_size=input_dim + 1,  # observation + time delta
          hidden_size=latent_dim
      )
      # Posterior distribution parameters
      self.mu_net = nn.Linear(latent_dim, latent_dim)
      self.logvar_net = nn.Linear(latent_dim, latent_dim)
    
    def forward(self, observations, times):
      """
      observations: (T, B, D) — observations at irregular times
      times: (T,) — observation timestamps
      Returns: z0_mu, z0_logvar for sampling initial state
      """
      batch_size = observations.size(1)
      h = torch.zeros(batch_size, self.latent_dim, device=observations.device)
      
      # Process in REVERSE time order (RNN reads future → past for encoding)
      obs_rev = torch.flip(observations, [0])
      times_rev = torch.flip(times, [0])
      
      for i in range(len(times_rev)):
        # ODE step from current time to next (in reverse)
        if i > 0:
          dt = times_rev[i-1] - times_rev[i]
          if dt > 0:
            t_span = torch.tensor([0., dt.item()])
            h = odeint(self.ode_func, h, t_span, 
                      method='dopri5', rtol=1e-4, atol=1e-5)[-1]
        
        # GRU update on observation
        dt_to_next = (times_rev[i] - times_rev[min(i+1, len(times_rev)-1)]).unsqueeze(0)
        gru_input = torch.cat([obs_rev[i], dt_to_next.expand(batch_size, 1)], dim=1)
        h = self.gru_cell(gru_input, h)
      
      return self.mu_net(h), self.logvar_net(h)

BUILD latent_ode_model.py:
- Full Latent ODE model combining encoder + ODE dynamics + decoder

  class PatientLatentODE(nn.Module):
    def __init__(self, 
                 obs_dim: int,        # number of biomarkers observed
                 latent_dim: int = 32,
                 hidden_dim: int = 64,
                 output_dim: int = None):  # None = same as obs_dim
      
      self.encoder = ODERNNEncoder(obs_dim, latent_dim, hidden_dim)
      self.ode_func = ODEFunc(latent_dim, hidden_dim)
      self.decoder = nn.Sequential(
          nn.Linear(latent_dim, hidden_dim), nn.ReLU(),
          nn.Linear(hidden_dim, output_dim or obs_dim)
      )
      # Uncertainty: separate variance decoder
      self.var_decoder = nn.Sequential(
          nn.Linear(latent_dim, hidden_dim), nn.ReLU(),
          nn.Linear(hidden_dim, output_dim or obs_dim),
          nn.Softplus()  # positive variance
      )
    
    def reparameterize(self, mu, logvar):
      return mu + torch.exp(0.5 * logvar) * torch.randn_like(mu)
    
    def forward(self, observations, obs_times, pred_times):
      # Encode observations → z0
      z0_mu, z0_logvar = self.encoder(observations, obs_times)
      z0 = self.reparameterize(z0_mu, z0_logvar)
      
      # Solve ODE forward from t=0 to prediction times
      # Using adjoint method for memory efficiency
      from torchdiffeq import odeint_adjoint as odeint
      z_traj = odeint(
          self.ode_func, z0, pred_times,
          method='dopri5',
          rtol=1e-4, atol=1e-5,
          adjoint_params=self.ode_func.parameters()
      )  # shape: (T_pred, B, latent_dim)
      
      # Decode trajectory
      pred_mean = self.decoder(z_traj)     # (T_pred, B, obs_dim)
      pred_var = self.var_decoder(z_traj)   # (T_pred, B, obs_dim)
      
      return pred_mean, pred_var, z0_mu, z0_logvar
    
    def predict_with_uncertainty(self, observations, obs_times, pred_times, 
                                  n_samples=50):
      """Monte Carlo uncertainty via multiple samples of z0"""
      samples = []
      for _ in range(n_samples):
        mean, _, _, _ = self.forward(observations, obs_times, pred_times)
        samples.append(mean)
      samples = torch.stack(samples)
      return samples.mean(0), samples.std(0)  # epistemic uncertainty
    
    def intervene(self, observations, obs_times, pred_times, 
                  intervention: dict):
      """
      Apply causal intervention: modify dynamics at specific time.
      intervention = {'time': t_int, 'variable': idx, 'value': val}
      """
      z0_mu, z0_logvar = self.encoder(observations, obs_times)
      z0 = self.reparameterize(z0_mu, z0_logvar)
      
      # Split pred_times at intervention point
      t_int = intervention['time']
      times_pre = pred_times[pred_times <= t_int]
      times_post = pred_times[pred_times > t_int]
      
      # Solve pre-intervention
      if len(times_pre) > 0:
        z_pre = odeint(self.ode_func, z0, times_pre, method='dopri5')[-1]
      else:
        z_pre = z0
      
      # Apply intervention in latent space
      z_intervened = self.apply_latent_intervention(z_pre, intervention)
      
      # Solve post-intervention with modified initial state
      if len(times_post) > 0:
        z_post = odeint(self.ode_func, z_intervened, 
                       torch.cat([t_int.unsqueeze(0), times_post]), 
                       method='dopri5')[1:]
        return self.decoder(z_post)
      return torch.empty(0)
```

---

### PHASE 3.2 — THREE ORGAN TWINS + TRAINING

```
Continuing PRISM Layer 3. Latent ODE architecture is complete.

TASK: Implement and train three specialized organ digital twins.

BUILD layer3_twin/organ_twins/cardiopulmonary_twin.py:
- Biomarkers: HR, SBP, DBP, SpO2, RR, BNP, eGFR, Troponin
- Target diseases: Heart failure, COPD, Pulmonary hypertension
- obs_dim = 8, latent_dim = 32, hidden_dim = 64
- Training data: MIMIC-IV cardiology admissions
  Filter: ICD codes I50 (heart failure), J44 (COPD), I27 (pulm hypertension)
  Minimum 72 hours of data

- DataModule (PyTorch Lightning):
  class CardiopulmonaryDataModule(pl.LightningDataModule):
    def setup(self, stage):
      # Load MIMIC-IV preprocessed data
      # Filter to cardiopulmonary cohort
      # Split: 70% train, 15% val, 15% test
      # Normalize per biomarker (save scalers)
    
    def collate_fn(batch):
      # Handle variable-length time series with masking
      # Pad to max length in batch
      # Create observation mask (1=observed, 0=missing)

- Training config:
  max_epochs: 200
  lr: 1e-3 → reduce on plateau (factor 0.5, patience 10)
  batch_size: 64
  loss: ELBO = reconstruction_mse + beta*KL, beta=1.0
  early_stopping: val_loss patience=20

- Validation metrics:
  MAE per biomarker at 24h, 48h, 72h prediction horizon
  AUROC for heart failure event prediction within 30 days
  Target: HR MAE < 5 BPM, SpO2 MAE < 2%

BUILD layer3_twin/organ_twins/metabolic_twin.py:
- Biomarkers: FBG, HbA1c, BMI, LDL, HDL, Triglycerides, TSH, Hemoglobin
- Target: T2DM progression, Metabolic syndrome, Anemia, Hypothyroidism
- Training data: NHANES (download script: scripts/download_nhanes.py)
  NHANES tables: DEMO, BMX, BPX, GHB, GLU, CBC, THYROID
  Longitudinal: NHANES has 2-year examination cycles → create trajectories
- Training config same as cardiopulmonary
- Additional: insulin resistance proxy (HOMA-IR = FBG * Insulin / 405)

BUILD layer3_twin/organ_twins/infectious_twin.py:
- Biomarkers: WBC, CRP, Temperature, Platelet, LDH, Ferritin, D-dimer
- Target: TB progression, Dengue severity, Sepsis trajectory
- Training data: PhysioNet 2019 Sepsis Challenge
  Download: physionet.org/content/challenge-2019/1.0.0/
  Also: MIMIC-IV patients with TB/dengue ICD codes
- CRITICAL: For sepsis, add 6-hour prediction window for septic shock
  Binary label: septic shock within 6 hours (AUROC target > 0.82)

BUILD layer3_twin/trainer.py:
class DigitalTwinTrainer:
  def train_all_twins(self, data_dir, output_dir):
    twins = {
      'cardiopulmonary': (CardiopulmonaryTwin(), CardiopulmonaryDataModule()),
      'metabolic': (MetabolicTwin(), MetabolicDataModule()),
      'infectious': (InfectiousTwin(), InfectiousDataModule())
    }
    for name, (twin, data) in twins.items():
      trainer = pl.Trainer(
          max_epochs=200,
          callbacks=[
              EarlyStopping('val_loss', patience=20),
              ModelCheckpoint(f'{output_dir}/{name}_best.ckpt', 
                            monitor='val_loss', save_top_k=1),
              LearningRateMonitor()
          ],
          logger=WandbLogger(project='prism-twins', name=name),
          accelerator='auto'  # uses GPU if available
      )
      trainer.fit(twin, data)
      self.evaluate_twin(twin, data, name)
  
  def evaluate_twin(self, twin, data, name):
    # Test set evaluation
    # Save: results/{name}_evaluation.json with all metrics
```

---

### PHASE 3.3 — RL INTERVENTION OPTIMIZER

```
Continuing PRISM. You have trained organ digital twins.

TASK: Build the RL-based intervention optimizer using PPO.

FILES TO CREATE:
layer4_rl/
├── __init__.py
├── patient_env.py
├── reward_functions.py
├── ppo_agent.py
├── cost_database.py
├── intervention_optimizer.py
└── tests/

BUILD cost_database.py:
INTERVENTIONS = {
    "nutritional_support": {
        "cost_govt": 0,          # ICDS scheme
        "cost_private": 800,     # ₹/month
        "side_effects": 0.01,
        "time_to_effect_days": 30,
        "qaly_weight": 0.15
    },
    "refer_phc": {
        "cost_govt": 0,
        "cost_private": 200,
        "side_effects": 0.0,
        "time_to_effect_days": 1,
        "qaly_weight": 0.05
    },
    "dots_tb_treatment": {
        "cost_govt": 0,          # RNTCP free
        "cost_private": 15000,   # ₹ 6-month course
        "side_effects": 0.12,
        "time_to_effect_days": 14,
        "qaly_weight": 2.1
    },
    "sputum_afb_test": {
        "cost_govt": 0,
        "cost_private": 150,
        "side_effects": 0.0,
        "time_to_effect_days": 2,
        "qaly_weight": 0.3  # diagnostic value
    },
    "iron_supplement": {
        "cost_govt": 0,          # NRHM free
        "cost_private": 120,     # ₹/month
        "side_effects": 0.05,
        "time_to_effect_days": 14,
        "qaly_weight": 0.8
    },
    "lifestyle_counseling": {
        "cost_govt": 0,
        "cost_private": 500,
        "side_effects": 0.0,
        "time_to_effect_days": 60,
        "qaly_weight": 0.4
    },
    "emergency_108": {
        "cost_govt": 0,
        "cost_private": 0,
        "side_effects": 0.0,
        "time_to_effect_days": 0,
        "qaly_weight": 3.0   # emergency
    }
}

BUILD patient_env.py:
class PatientHealthEnv(gymnasium.Env):
  """
  MDP environment for patient health management.
  State: patient health features + trajectory + causal weights
  Action: intervention selection
  Reward: QALY gain - cost - side effects
  """
  def __init__(self, patient_cohort, digital_twin, cost_db,
               episode_length_months=12):
    super().__init__()
    
    N_ACTIONS = len(INTERVENTIONS)
    N_STATE_FEATURES = 30  # biomarkers + trajectory features + demographics
    
    self.action_space = gymnasium.spaces.Discrete(N_ACTIONS)
    self.observation_space = gymnasium.spaces.Box(
        low=-np.inf, high=np.inf, 
        shape=(N_STATE_FEATURES,), dtype=np.float32
    )
    
    self.patient_cohort = patient_cohort
    self.twin = digital_twin
    self.cost_db = cost_db
    self.episode_length = episode_length_months * 30  # days
  
  def reset(self, seed=None, options=None):
    # Sample random patient from cohort
    self.current_patient = random.choice(self.patient_cohort)
    self.current_day = 0
    self.applied_interventions = []
    self.patient_state = self._get_initial_state()
    return self._get_observation(), {}
  
  def step(self, action):
    intervention = list(INTERVENTIONS.keys())[action]
    
    # Apply intervention to digital twin
    new_state = self.twin.intervene(
        self.patient_state, intervention, self.current_day)
    
    # Compute reward
    reward = self._compute_reward(
        self.patient_state, new_state, intervention)
    
    self.patient_state = new_state
    self.current_day += 30  # monthly decisions
    self.applied_interventions.append(intervention)
    
    done = self.current_day >= self.episode_length
    truncated = False
    
    return self._get_observation(), reward, done, truncated, {}
  
  def _compute_reward(self, old_state, new_state, intervention):
    # QALY improvement
    qaly_gain = compute_qaly_gain(old_state, new_state) * 365
    
    # Cost (normalized by monthly income bracket)
    income_brackets = [5000, 10000, 20000, 50000]  # ₹/month
    income = self.current_patient.get('monthly_income', 8000)
    cost_normalized = INTERVENTIONS[intervention]['cost_private'] / income
    
    # Side effect penalty
    side_effect_penalty = INTERVENTIONS[intervention]['side_effects'] * 10
    
    # Unnecessary intervention penalty (discourage over-treatment)
    redundancy_penalty = 0.1 if intervention in self.applied_interventions else 0
    
    return qaly_gain - cost_normalized - side_effect_penalty - redundancy_penalty

BUILD ppo_agent.py:
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import EvalCallback

def train_ppo_agent(env_fn, n_envs=8, total_timesteps=2_000_000):
  # Vectorized environments for faster training
  vec_env = SubprocVecEnv([env_fn for _ in range(n_envs)])
  eval_env = SubprocVecEnv([env_fn for _ in range(2)])
  
  model = PPO(
      "MlpPolicy",
      vec_env,
      policy_kwargs=dict(
          net_arch=dict(pi=[256, 256, 128], vf=[256, 256, 128]),
          activation_fn=nn.ReLU
      ),
      learning_rate=3e-4,
      n_steps=2048,
      batch_size=64,
      n_epochs=10,
      gamma=0.99,
      gae_lambda=0.95,
      clip_range=0.2,
      ent_coef=0.01,       # entropy bonus for exploration
      vf_coef=0.5,
      max_grad_norm=0.5,
      verbose=1,
      tensorboard_log="./tb_logs/ppo_prism/"
  )
  
  eval_callback = EvalCallback(
      eval_env,
      best_model_save_path='./models/best_ppo/',
      eval_freq=10000,
      deterministic=True
  )
  
  model.learn(
      total_timesteps=total_timesteps,
      callback=eval_callback,
      progress_bar=True
  )
  return model

BUILD intervention_optimizer.py (main interface):
class PRISMInterventionOptimizer:
  def __init__(self, ppo_model_path, twin_models_dir, cost_db):
    self.ppo = PPO.load(ppo_model_path)
    self.twins = load_all_twins(twin_models_dir)
    self.cost_db = cost_db
  
  def optimize(self, patient_state, n_recommendations=3) -> InterventionPlan:
    # Get RL policy recommendation
    obs = patient_state_to_observation(patient_state)
    action, _ = self.ppo.predict(obs, deterministic=True)
    
    # Get top-N by running policy with slight noise
    top_actions = self.get_top_n_actions(obs, n=n_recommendations)
    
    # Score each action with multi-objective metrics
    recommendations = []
    for action in top_actions:
      intervention = list(INTERVENTIONS.keys())[action]
      
      # Simulate effect via digital twin
      projected_state = self.twins.intervene(patient_state, intervention)
      
      recommendations.append(InterventionRecommendation(
          intervention=intervention,
          description=INTERVENTIONS[intervention],
          projected_disease_reduction=compute_reduction(
              patient_state, projected_state),
          cost_govt=INTERVENTIONS[intervention]['cost_govt'],
          cost_private=INTERVENTIONS[intervention]['cost_private'],
          qaly_gain=compute_qaly(patient_state, projected_state),
          cost_per_qaly=compute_cost_per_qaly(intervention, patient_state, projected_state),
          time_to_effect=INTERVENTIONS[intervention]['time_to_effect_days'],
          evidence_level="B"  # TODO: link to clinical evidence database
      ))
    
    # Pareto-optimal ranking
    pareto_front = compute_pareto_front(
        recommendations, 
        objectives=['projected_disease_reduction', 'cost_govt'])
    
    return InterventionPlan(
        recommendations=pareto_front,
        primary_recommendation=pareto_front[0],
        narrative=self.build_intervention_narrative(pareto_front[0])
    )
```

---
---

# PERSON 4: PLATFORM ENGINEER
## Backend + Frontend + ABDM + Federated Learning + Android

---

### PHASE 4.1 — FASTAPI BACKEND + SUPABASE

```
You are building PRISM. You are Person 4 — Platform Engineer.
Responsible for backend, frontend, ABDM, FL, and Android integration.

TASK: Build the complete FastAPI backend with Supabase integration.

PROJECT STRUCTURE:
prism/
├── backend/
│   ├── main.py
│   ├── routers/
│   │   ├── patients.py
│   │   ├── diagnostics.py
│   │   ├── abdm.py
│   │   └── federated.py
│   ├── services/
│   │   ├── inference_service.py
│   │   ├── abdm_service.py
│   │   └── report_service.py
│   ├── models/
│   │   ├── patient.py
│   │   ├── diagnostic_result.py
│   │   └── report.py
│   ├── db/
│   │   ├── supabase_client.py
│   │   └── schema.sql
│   └── utils/
│       ├── auth.py
│       └── encryption.py

REQUIREMENTS (add):
fastapi==0.109.0
uvicorn==0.27.0
supabase==2.3.4
pydantic==2.5.3
python-multipart==0.0.9
celery==5.3.6
redis==5.0.1
httpx==0.26.0
python-jose==3.3.0
cryptography==42.0.2
fhir.resources==7.1.0

BUILD db/schema.sql (Supabase PostgreSQL):
-- Patients table
CREATE TABLE patients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  abha_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  encrypted_demographics BYTEA,  -- AES-256 encrypted
  consent_given BOOLEAN DEFAULT FALSE,
  consent_timestamp TIMESTAMPTZ
);

-- Diagnostic sessions
CREATE TABLE diagnostic_sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID REFERENCES patients(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  session_type TEXT CHECK (session_type IN ('full','audio_only','visual_only','rppg_only')),
  
  -- Layer 1 results
  sense_results JSONB,
  
  -- Layer 2 results
  causal_results JSONB,
  
  -- Layer 3 results  
  twin_trajectory JSONB,
  
  -- Layer 4 results
  intervention_plan JSONB,
  
  -- Final report
  disease_probabilities JSONB,  -- {disease: probability, ...}
  primary_diagnosis TEXT,
  confidence_score FLOAT CHECK (confidence_score BETWEEN 0 AND 1),
  uncertainty_bounds JSONB,
  
  -- Clinical validation
  doctor_validated BOOLEAN DEFAULT FALSE,
  doctor_id UUID,
  ground_truth_diagnosis TEXT
);

-- Clinical reports
CREATE TABLE clinical_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID REFERENCES diagnostic_sessions(id),
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  report_pdf_url TEXT,  -- Supabase storage URL
  abdm_push_status TEXT CHECK (abdm_push_status IN ('pending','success','failed')),
  abdm_record_id TEXT
);

-- Federated learning rounds
CREATE TABLE fl_rounds (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  round_number INT,
  participating_nodes INT,
  global_model_version TEXT,
  aggregation_timestamp TIMESTAMPTZ DEFAULT NOW(),
  metrics JSONB
);

-- Row Level Security
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE diagnostic_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "patients_own_data" ON patients FOR ALL 
  USING (auth.uid()::TEXT = id::TEXT);

BUILD backend/main.py:
from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI(
    title="PRISM API",
    description="Passive Readings Intelligent Scalable Medicine",
    version="1.0.0"
)

app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://prism-health.vercel.app"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(patients.router, prefix="/api/v1/patients", tags=["patients"])
app.include_router(diagnostics.router, prefix="/api/v1/diagnostics", tags=["diagnostics"])
app.include_router(abdm.router, prefix="/api/v1/abdm", tags=["abdm"])
app.include_router(federated.router, prefix="/api/v1/federated", tags=["federated"])

BUILD routers/diagnostics.py:
@router.post("/analyze")
async def run_full_analysis(
    audio_file: UploadFile = File(None),
    video_file: UploadFile = File(None),
    patient_features: PatientFeaturesSchema = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user = Depends(get_current_user)
):
  # 1. Save files to Supabase storage
  session_id = str(uuid4())
  
  # 2. Queue analysis jobs via Celery
  task = celery_app.send_task('run_prism_analysis', args=[{
      'session_id': session_id,
      'audio_path': audio_path,
      'video_path': video_path,
      'patient_features': patient_features.dict()
  }])
  
  return {"session_id": session_id, "task_id": task.id, "status": "processing"}

@router.get("/results/{session_id}")
async def get_results(session_id: str, current_user = Depends(get_current_user)):
  session = await supabase.table('diagnostic_sessions')\
      .select('*').eq('id', session_id).single().execute()
  return DiagnosticResultResponse(**session.data)

@router.get("/stream/{session_id}")
async def stream_results(session_id: str, request: Request):
  """Server-Sent Events for real-time progress updates"""
  async def event_generator():
    while True:
      status = await get_analysis_status(session_id)
      yield f"data: {status.json()}\n\n"
      if status.completed:
        break
      await asyncio.sleep(1)
  return EventSourceResponse(event_generator())
```

---

### PHASE 4.2 — NEXT.JS 14 CLINICAL DASHBOARD

```
Continuing PRISM Platform. Backend is running.

TASK: Build the production clinical dashboard in Next.js 14.
Design style: Medical-grade precision. Dark theme with electric blue 
and surgical white accents. No generic healthcare stock design.
Think: mission control meets clinical ICU monitoring.

STACK: Next.js 14 App Router, shadcn/ui, Tailwind CSS, Recharts, Framer Motion

PROJECT: frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx              (landing/login)
│   ├── dashboard/
│   │   ├── page.tsx          (main dashboard)
│   │   └── layout.tsx
│   ├── patient/
│   │   ├── [id]/page.tsx     (patient detail)
│   │   └── new/page.tsx      (new scan)
│   └── scan/
│       └── page.tsx          (live scan page)
├── components/
│   ├── scan/
│   │   ├── CameraCapture.tsx
│   │   ├── AudioCapture.tsx
│   │   └── ScanProgress.tsx
│   ├── results/
│   │   ├── DiseaseProbabilityCard.tsx
│   │   ├── CausalGraphViz.tsx
│   │   ├── TrajectoryChart.tsx
│   │   ├── InterventionPlan.tsx
│   │   └── UncertaintyBands.tsx
│   ├── dashboard/
│   │   ├── PatientQueue.tsx
│   │   └── StatsOverview.tsx
│   └── ui/                   (shadcn components)
└── lib/
    ├── api.ts
    └── types.ts

BUILD components/results/TrajectoryChart.tsx:
- Uses Recharts ComposedChart
- Shows: disease biomarker trajectory over 12 months
- Two lines: current trajectory (red dashed) vs with intervention (green solid)
- Confidence bands as gray shaded area (Area chart behind lines)
- Vertical line at "today" 
- Vertical line at "intervention point"
- X-axis: months 0-18
- Annotations: "Critical threshold", "Without intervention: active TB ~month 5"
- Animated: lines draw in on mount (Recharts animation + Framer Motion)
- Responsive: recharts ResponsiveContainer
- Color scheme: background #0a0f1e, lines #22c55e and #ef4444, 
  confidence band rgba(100,100,255,0.15)

BUILD components/results/CausalGraphViz.tsx:
- Interactive causal graph using D3.js force simulation (npm i d3)
- Nodes: biomarkers + disease (circles)
- Edges: causal arrows with thickness = effect strength
- Node color: red = disease, blue = biomarker, orange = risk factor
- On hover: show edge weight + p-value tooltip
- On click disease node: highlight all causal paths
- Animation: nodes appear one by one on mount
- Include: Anthropic API call to explain selected edge in plain language
  "Why does malnutrition cause TB?" → Claude explains in 1 sentence

BUILD components/scan/CameraCapture.tsx:
- Uses browser MediaDevices API
- Shows live camera feed with overlaid face landmark points
- Real-time rPPG: show updating HR estimate as scan progresses
- Progress bar: "Scan quality: 67%" updating in real-time
- Face detection indicator: green ring when face detected, red when lost
- Time remaining countdown: 30 seconds total
- Submit button: appears after 30 seconds
- State machine: IDLE → DETECTING_FACE → SCANNING → COMPLETE → ERROR

BUILD app/patient/[id]/page.tsx:
- Complete patient detail page
- Sections:
  1. Header: patient ID (anonymized), scan date, overall risk score
  2. Disease probability grid: 12 disease cards with probability + trend
  3. Top diagnosis: large card with full causal analysis
  4. Trajectory chart: interactive, toggle intervention scenarios
  5. Intervention plan: ranked list with cost badges (₹0 FREE tag for govt)
  6. Causal graph: full interactive visualization
  7. Historical scans: timeline of past diagnostic sessions
  8. Export: PDF report button, ABDM push button

BUILD lib/api.ts:
const API_BASE = process.env.NEXT_PUBLIC_API_URL

export const prismAPI = {
  startScan: (data: ScanRequest) => 
    fetch(`${API_BASE}/diagnostics/analyze`, {method:'POST', body: ...}),
  
  getResults: (sessionId: string) => 
    fetch(`${API_BASE}/diagnostics/results/${sessionId}`),
  
  streamResults: (sessionId: string, onUpdate: (data: any) => void) => {
    const es = new EventSource(`${API_BASE}/diagnostics/stream/${sessionId}`)
    es.onmessage = (e) => onUpdate(JSON.parse(e.data))
    return () => es.close()
  },
  
  pushToABDM: (sessionId: string, abhaId: string) =>
    fetch(`${API_BASE}/abdm/push`, {method:'POST', ...})
}
```

---

### PHASE 4.3 — ABDM/ABHA INTEGRATION

```
Continuing PRISM Platform. Dashboard is built.

TASK: Build complete ABDM/ABHA integration for India's national health stack.

BUILD backend/services/abdm_service.py:

ABDM SANDBOX ENDPOINTS:
  BASE_URL = "https://dev.abdm.gov.in/gateway"
  AUTH_URL = "https://dev.abdm.gov.in/gateway/v0.5/sessions"

class ABDMService:
  def __init__(self, client_id: str, client_secret: str):
    self.client_id = client_id
    self.client_secret = client_secret
    self.access_token = None
    self.token_expiry = None
  
  async def authenticate(self):
    """Get access token from ABDM gateway"""
    resp = await httpx.AsyncClient().post(
        f"{AUTH_URL}",
        json={"clientId": self.client_id, "clientSecret": self.client_secret}
    )
    data = resp.json()
    self.access_token = data['accessToken']
    self.token_expiry = datetime.now() + timedelta(seconds=data['expiresIn'])
  
  async def verify_abha(self, abha_id: str) -> ABHAProfile:
    """Verify ABHA ID and get basic profile"""
    await self.ensure_authenticated()
    resp = await self.client.get(
        f"{BASE_URL}/v0.5/patients/profile",
        headers={"Authorization": f"Bearer {self.access_token}",
                 "X-CM-ID": "sbx"},
        params={"healthId": abha_id}
    )
    return ABHAProfile(**resp.json())
  
  async def request_health_records(
      self, abha_id: str, date_from: str, date_to: str
  ) -> List[HealthRecord]:
    """
    Fetch patient's health records via ABDM Health Information Flow
    Steps: Consent Request → Consent Artifact → Health Information
    """
    # Step 1: Create consent request
    consent_id = await self.create_consent_request(
        abha_id=abha_id,
        hi_types=["DiagnosticReport", "Prescription", "OPConsultation"],
        date_from=date_from, date_to=date_to,
        purpose="CAREMGT"  # Care management
    )
    
    # Step 2: Wait for consent approval (webhook in production)
    # In demo: use pre-approved test patient
    consent_artifact = await self.poll_consent_status(consent_id, timeout_s=30)
    
    # Step 3: Fetch health information
    health_info = await self.fetch_health_info(consent_artifact)
    
    # Step 4: Parse FHIR R4 resources
    return self.parse_fhir_bundle(health_info)
  
  async def push_diagnostic_report(
      self, abha_id: str, prism_report: DiagnosticResult
  ) -> str:
    """Push PRISM diagnostic result to patient's ABHA health locker"""
    from fhir.resources.diagnosticreport import DiagnosticReport
    from fhir.resources.observation import Observation
    
    # Build FHIR DiagnosticReport resource
    observations = []
    for disease, prob in prism_report.disease_probabilities.items():
      obs = Observation(
          status="final",
          code={"coding": [{"system": "http://loinc.org", 
                             "code": DISEASE_LOINC_CODES[disease]}]},
          valueQuantity={"value": prob, "unit": "probability"},
          note=[{"text": f"PRISM AI diagnostic. Confidence: {prob:.2%}"}]
      )
      observations.append(obs)
    
    report = DiagnosticReport(
        status="final",
        code={"coding": [{"display": "PRISM Multimodal Diagnostic Report"}]},
        subject={"identifier": {"value": abha_id}},
        result=[{"reference": f"Observation/{o.id}"} for o in observations],
        conclusion=prism_report.primary_diagnosis,
        presentedForm=[{
            "contentType": "application/pdf",
            "url": prism_report.pdf_url
        }]
    )
    
    # Push to ABDM
    resp = await self.client.post(
        f"{BASE_URL}/v0.5/health-information/notify",
        json=report.dict(), 
        headers=self.get_headers()
    )
    return resp.json()['id']
  
  def parse_fhir_bundle(self, fhir_data: dict) -> List[HealthRecord]:
    """Parse FHIR R4 Bundle → structured health records for digital twin"""
    records = []
    for entry in fhir_data.get('entry', []):
      resource = entry.get('resource', {})
      resource_type = resource.get('resourceType')
      
      if resource_type == 'DiagnosticReport':
        records.append(HealthRecord(
            type='diagnostic',
            date=resource['effectiveDateTime'],
            findings=resource.get('conclusion', ''),
            codes=[c['code'] for c in resource.get('code', {}).get('coding', [])]
        ))
      elif resource_type == 'Observation':
        records.append(HealthRecord(
            type='observation',
            date=resource['effectiveDateTime'],
            parameter=resource['code']['coding'][0]['display'],
            value=resource.get('valueQuantity', {}).get('value'),
            unit=resource.get('valueQuantity', {}).get('unit')
        ))
    return records

BUILD backend/routers/abdm.py:
@router.post("/verify/{abha_id}")
async def verify_abha_patient(abha_id: str):
  profile = await abdm_service.verify_abha(abha_id)
  return {"verified": True, "name": profile.name, "age": profile.age}

@router.post("/fetch-history/{abha_id}")
async def fetch_patient_history(abha_id: str, date_from: str, date_to: str):
  records = await abdm_service.request_health_records(abha_id, date_from, date_to)
  twin_input = convert_records_to_twin_format(records)
  return {"records_count": len(records), "twin_input": twin_input}

@router.post("/push-report")
async def push_report_to_abdm(session_id: str, abha_id: str):
  report = await get_diagnostic_result(session_id)
  abdm_id = await abdm_service.push_diagnostic_report(abha_id, report)
  await supabase.table('clinical_reports').update(
      {'abdm_push_status': 'success', 'abdm_record_id': abdm_id}
  ).eq('session_id', session_id).execute()
  return {"status": "success", "abdm_record_id": abdm_id}
```

---

### PHASE 4.4 — FEDERATED LEARNING SERVER

```
Continuing PRISM Platform.

TASK: Set up Flower federated learning server and hospital client.

BUILD backend/federated/fl_server.py:
import flwr as fl
from flwr.server.strategy import FedAvg
import numpy as np

class PRISMFederatedStrategy(FedAvg):
  """
  Custom FL strategy with:
  - Differential privacy noise addition
  - Secure aggregation
  - Model quality filtering (reject bad updates)
  """
  def __init__(self, dp_epsilon=1.0, dp_delta=1e-5, min_clients=2, **kwargs):
    super().__init__(min_fit_clients=min_clients, 
                     min_evaluate_clients=min_clients,
                     min_available_clients=min_clients, **kwargs)
    self.dp_epsilon = dp_epsilon
    self.dp_delta = dp_delta
    self.round_metrics = []
  
  def aggregate_fit(self, server_round, results, failures):
    # Filter: reject updates from clients with loss > 3*median
    losses = [r.metrics.get('train_loss', 0) for _, r in results]
    median_loss = np.median(losses)
    filtered = [(c, r) for c, r in results 
                if r.metrics.get('train_loss', 0) <= 3 * median_loss]
    
    # Aggregate weights
    aggregated = super().aggregate_fit(server_round, filtered, failures)
    
    if aggregated:
      weights, metrics = aggregated
      
      # Add calibrated Gaussian noise for differential privacy
      noisy_weights = self.add_dp_noise(weights)
      
      # Log round metrics
      self.round_metrics.append({
          'round': server_round,
          'n_clients': len(filtered),
          'n_rejected': len(results) - len(filtered),
          'metrics': metrics
      })
      
      return noisy_weights, metrics
    return aggregated
  
  def add_dp_noise(self, weights):
    """Add Gaussian noise calibrated to (epsilon, delta)-DP"""
    sensitivity = 2.0  # L2 sensitivity of federated averaging
    noise_std = sensitivity * np.sqrt(2 * np.log(1.25 / self.dp_delta)) / self.dp_epsilon
    
    return [
        np.array(w) + np.random.normal(0, noise_std, np.array(w).shape)
        for w in weights
    ]

def start_fl_server(port=8080, num_rounds=100):
  strategy = PRISMFederatedStrategy(
      dp_epsilon=1.0, dp_delta=1e-5,
      min_clients=2,
      initial_parameters=load_initial_global_model()
  )
  
  fl.server.start_server(
      server_address=f"0.0.0.0:{port}",
      config=fl.server.ServerConfig(num_rounds=num_rounds),
      strategy=strategy
  )

BUILD backend/federated/fl_client.py:
class PRISMHospitalClient(fl.client.NumPyClient):
  """
  Runs at each hospital. 
  Trains on local data. Never sends data to server.
  Only sends model weight UPDATES (encrypted).
  """
  def __init__(self, model, local_data_path: str, hospital_id: str):
    self.model = model
    self.local_data = load_hospital_data(local_data_path)  # stays local
    self.hospital_id = hospital_id
  
  def get_parameters(self, config):
    return get_model_parameters(self.model)
  
  def set_parameters(self, parameters):
    set_model_parameters(self.model, parameters)
  
  def fit(self, parameters, config):
    # Set global model weights
    self.set_parameters(parameters)
    
    # Train on LOCAL data only (never leaves hospital)
    train_loss, n_samples = train_local(
        self.model, self.local_data, 
        epochs=config.get('local_epochs', 3),
        lr=config.get('lr', 1e-4)
    )
    
    # Clip gradients before sending (DP mechanism)
    clipped_params = clip_model_updates(
        parameters, self.get_parameters(config), 
        max_norm=1.0
    )
    
    return clipped_params, n_samples, {"train_loss": train_loss}
  
  def evaluate(self, parameters, config):
    self.set_parameters(parameters)
    loss, accuracy = evaluate_local(self.model, self.local_data)
    return loss, len(self.local_data), {"accuracy": accuracy}
```

---

### PHASE 4.5 — ANDROID APP + COMPLETE INTEGRATION

```
Continuing PRISM Platform.

TASK: Create Android integration module specification and 
end-to-end system integration tests.

BUILD android_app/PRISMAndroidModule.kt (Kotlin):
class PRISMModule(private val context: Context) {
  
  // TFLite model runners
  private lateinit var coughClassifier: Interpreter
  private lateinit var rppgProcessor: Interpreter
  private lateinit var visualClassifier: Interpreter
  private lateinit var fusionModel: Interpreter
  
  fun initialize() {
    // Load TFLite models from assets
    coughClassifier = Interpreter(loadModel("cough_classifier.tflite"),
        Interpreter.Options().apply { numThreads = 4; useNNAPI = true })
    rppgProcessor = Interpreter(loadModel("rppg_processor.tflite"),
        Interpreter.Options().apply { numThreads = 4 })
    visualClassifier = Interpreter(loadModel("visual_classifier.tflite"),
        Interpreter.Options().apply { useGPU = true })
    fusionModel = Interpreter(loadModel("fusion_model.tflite"))
  }
  
  suspend fun runFullDiagnostic(
    videoFile: File,
    audioFile: File,
    patientFeatures: PatientFeatures
  ): DiagnosticResult = withContext(Dispatchers.Default) {
    
    // Run all 3 on-device models in parallel
    val (rppgResult, audioResult, visualResult) = awaitAll(
      async { runrPPGAnalysis(videoFile) },
      async { runAudioAnalysis(audioFile) },
      async { runVisualAnalysis(videoFile) }
    )
    
    // Fuse on-device
    val senseResult = runFusion(rppgResult, audioResult, visualResult)
    
    // If online: send to backend for Layer 2+3+4 analysis
    // If offline: return sense result only with "offline mode" flag
    return@withContext if (isNetworkAvailable()) {
      val fullResult = apiClient.runFullAnalysis(senseResult, patientFeatures)
      fullResult
    } else {
      DiagnosticResult(senseResult = senseResult, offlineMode = true)
    }
  }
  
  private fun runAudioAnalysis(audioFile: File): AudioResult {
    // Load audio, preprocess, run TFLite
    val waveform = loadAudioAsFloat(audioFile, targetSr = 22050)
    val melSpec = computeMelSpectrogram(waveform)  // (128, T) float array
    val inputBuffer = ByteBuffer.allocateDirect(128 * T * 4)
    inputBuffer.order(ByteOrder.nativeOrder())
    // Fill buffer...
    val output = Array(1) { FloatArray(8) }
    coughClassifier.run(inputBuffer, output)
    return AudioResult(diseaseProbs = output[0].toList())
  }
}

BUILD integration tests (tests/integration/test_end_to_end.py):
class TestPRISMEndToEnd:
  
  def test_full_pipeline_tb_patient(self):
    """
    End-to-end test: simulated TB patient → correct diagnosis
    Uses: synthetic audio (TB cough pattern), synthetic video (facial pallor)
    """
    # Generate synthetic inputs
    tb_audio = generate_synthetic_tb_cough(duration_s=30)
    pallor_video = generate_synthetic_pallor_video(frames=900)
    patient_features = {
        "nutrition_score": 3.0, "bmi": 17.5, "age": 32,
        "crowding_index": 4.2, "smoking": 0
    }
    
    # Run full pipeline
    result = prism_pipeline.run_full(tb_audio, pallor_video, patient_features)
    
    # Assertions
    assert result.disease_probabilities["TB"] > 0.60
    assert result.causal_attributions is not None
    assert len(result.top_interventions) >= 2
    assert result.trajectory_months_to_active is not None
    assert result.uncertainty_bounds["TB"]["lower"] < result.disease_probabilities["TB"]
    assert result.uncertainty_bounds["TB"]["upper"] > result.disease_probabilities["TB"]
  
  def test_offline_mode(self):
    """Verify system works without internet (Layer 1 only)"""
    with mock_network_unavailable():
      result = android_module.run_full_diagnostic(
          test_audio, test_video, test_features)
    assert result.offline_mode == True
    assert result.sense_result is not None
    # No causal/twin/RL results in offline mode
    assert result.causal_results is None
  
  def test_response_time(self):
    """Full pipeline < 3 seconds on server"""
    import time
    start = time.time()
    result = prism_pipeline.run_full(test_audio, test_video, test_features)
    elapsed = time.time() - start
    assert elapsed < 3.0, f"Pipeline took {elapsed:.2f}s, target < 3.0s"
  
  def test_abdm_integration(self):
    """ABDM sandbox: verify records fetch and push"""
    # Uses ABDM sandbox test patient
    TEST_ABHA_ID = "91-1234-5678-1234"
    profile = abdm_service.verify_abha(TEST_ABHA_ID)
    assert profile.verified == True
    
    records = abdm_service.request_health_records(
        TEST_ABHA_ID, "2023-01-01", "2024-01-01")
    assert len(records) >= 0  # May be empty for test patient
  
  def test_federated_round(self):
    """Simulate 2-client FL round, verify model improves"""
    initial_loss = evaluate_global_model()
    simulate_fl_round(n_clients=2, local_epochs=3)
    final_loss = evaluate_global_model()
    assert final_loss <= initial_loss * 1.05  # Should not degrade > 5%
```

---

## INTEGRATION PROTOCOL (All 4 Persons)

### Week-End Sync Format
Each person pushes to their branch: `p1/sense`, `p2/reason`, `p3/twin-rl`, `p4/platform`

Person 4 merges to `dev` every Friday. Run integration test suite.

### Interface Contracts (Do Not Break)

**Person 1 → Person 2 (Layer 1 → Layer 2 input):**
```python
SenseResult = {
    "disease_probabilities": Dict[str, float],  # 12 diseases, 0-1
    "rppg": {"hr": float, "spo2": float, "hrv_rmssd": float, "rr": float},
    "audio": {"cough_detected": bool, "disease_probs": Dict[str, float]},
    "visual": {"jaundice": float, "anemia": float, "cyanosis": float},
    "uncertainty": Dict[str, Tuple[float, float]],  # lower, upper bounds
    "processing_time_ms": int
}
```

**Person 2 → Person 3 (Layer 2 → Layer 3 input):**
```python
CausalResult = {
    "attributions": Dict[str, float],  # cause → weight, sums to 1
    "top_intervention": str,
    "intervention_effects": Dict[str, float],  # intervention → prob_reduction
    "patient_risk_factors": Dict[str, float],  # normalized risk scores
    "counterfactuals": List[Dict]
}
```

**Person 3 → Person 4 (Layer 3+4 → API output):**
```python
TwinRLResult = {
    "trajectory": {
        "without_intervention": List[Dict],  # [{month: t, prob: p}, ...]
        "with_best_intervention": List[Dict]
    },
    "months_to_critical": float,
    "intervention_plan": List[InterventionRecommendation],
    "qaly_gain_estimate": float
}
```

### Git Commit Convention
```
p1: [SENSE] feature description
p2: [REASON] feature description
p3: [TWIN] or [RL] feature description
p4: [PLATFORM] feature description
[ALL] integration: description
```

---

*PRISM Build Prompts v1.0 — Team of 4 | 10 Months | Win*