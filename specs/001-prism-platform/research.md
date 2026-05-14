# Research & Decisions: PRISM Layer 1 (SENSE)

**Decision**: Use MediaPipe FaceMesh for face detection and ROI extraction.
**Rationale**: Runs in real-time (30fps) on edge devices without requiring a heavy GPU. Provides 468 precise 3D facial landmarks which are necessary for extracting isolated ROIs (forehead, left/right cheeks, sclera, conjunctiva) while rejecting noise from background and hair.
**Alternatives considered**: Dlib (too slow/heavy for edge), OpenCV Haar cascades (not accurate enough for precise ROI landmarks).

**Decision**: Use CHROM method for rPPG signal extraction.
**Rationale**: Chrominance-based method (CHROM) is highly robust to motion artifacts by using a linear combination of RGB channels to eliminate specular reflection. This is essential for unconstrained smartphone captures.
**Alternatives considered**: POS (Plane-Orthogonal to Skin) and Green-channel only. CHROM performs better under varying lighting conditions.

**Decision**: Fine-tune YAMNet for cough/respiratory classification.
**Rationale**: YAMNet is already trained on AudioSet and serves as a highly robust general audio feature extractor. Freezing the backbone and training a custom classification head on COUGHVID and Coswara datasets avoids overfitting on limited clinical audio samples.
**Alternatives considered**: Training a CNN from scratch on Mel-spectrograms (requires too much data), VGGish (heavier footprint than YAMNet).

**Decision**: Use MobileNetV3-Large with multi-task heads for visual biomarkers.
**Rationale**: MobileNetV3 is optimized for mobile CPU/DSP inference. A multi-task head allows a single backbone feature extraction to simultaneously predict jaundice, anemia, cyanosis, and dengue flush, saving massive amounts of compute compared to running 4 separate models.
**Alternatives considered**: ResNet50 (too slow for Android), EfficientNet (harder to quantize to INT8).

**Decision**: Fuse modalities using Cross-Modal Attention.
**Rationale**: Attention mechanisms can natively handle missing modalities (using masking) and learn complex interactions (e.g. pale face + abnormal breathing is worse than the sum of its parts).
**Alternatives considered**: Simple early concatenation (fails if a modality is missing), Late averaging of probabilities (fails to capture interactions).

**Decision**: Export all models to TFLite with FP16/INT8 quantization.
**Rationale**: TFLite is the standard for Android on-device inference. Quantization reduces model size (target < 15MB) and inference time without significant accuracy loss.
**Alternatives considered**: ONNX Runtime Mobile (used as a fallback, but TFLite integrates better with Android CameraX).
