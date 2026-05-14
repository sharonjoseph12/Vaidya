# Android Integration Specification

This directory contains the scaffolding for the PRISM Android application targeting on-device diagnostics.

## TFLite Integration Requirements (For Person 1)
Please ensure your `.tflite` models conform to the following specifications for integration into `PRISMModule.kt`:

1. **`audio_classifier.tflite`**
   - **Input Shape**: `[1, 128, 128, 1]` (Mel spectrogram)
   - **Output Shape**: `[1, 8]` (Probabilities for 8 classes)
2. **`visual_classifier.tflite`**
   - **Input Shape**: `[1, 224, 224, 3]` (Cropped ROI)
   - **Output Shape**: `[1, 4]` (Probabilities for Anemia, Jaundice, Cyanosis, Healthy)
3. **`fusion_model.tflite`**
   - **Input Shape**: `[1, 12]` (Concatenated embeddings)
   - **Output Shape**: `[1, 8]` (Final fused predictions)

## Deployment
Place models in `prism/android_app/app/src/main/assets/`.
