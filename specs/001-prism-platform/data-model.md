# Data Model: PRISM Layer 1 (SENSE)

## VitalsResult (rPPG Output)
- `hr`: Float (Heart rate in BPM)
- `spo2`: Float (Oxygen saturation percentage, clamped 85-100)
- `hrv_rmssd`: Float (Root mean square of successive differences in ms)
- `hrv_sdnn`: Float (Standard deviation of NN intervals in ms)
- `lf_hf_ratio`: Float (Low-frequency to High-frequency ratio)
- `rr`: Float (Respiratory rate in breaths/min)
- `confidence_scores`: Dict[String, Float] (Signal-to-noise ratio or model confidence per metric)

## CoughSegment (Audio Pre-processing)
- `start_time`: Float (Seconds)
- `end_time`: Float (Seconds)
- `confidence`: Float (CNN probability of being a true cough)

## AcousticFeatures (Audio Input to Classifier)
- `mel_spectrogram`: Array[128, T]
- `mfcc_features`: Array[120, T]
- `chroma_stft`: Array[12, T]
- `spectral_features`: Array[5, T]
- `temporal_features`: Dict[String, Float] (duration, peak amplitude, decay rate, attack time)

## AudioAnalysisResult
- `cough_detected`: Boolean
- `breathing_rate`: Float
- `abnormal_sounds`: Dict[String, String] (Wheeze: mild, Crackle: none, Stridor: severe)
- `voice_biomarkers`: VoiceBiomarkers (jitter, shimmer, hnr)
- `disease_probs`: Dict[String, Float] (8 respiratory classes)

## FaceROIs (Visual Pre-processing)
- `forehead`: Array (Mask + Cropped RGB)
- `left_cheek`: Array
- `right_cheek`: Array
- `sclera`: Array
- `conjunctiva`: Array
- `lips`: Array

## ColorBiomarkers (Visual Output)
- `jaundice_score`: Float
- `jaundice_severity`: String (none/mild/moderate/severe)
- `pallor_score`: Float
- `cyanosis_score`: Float
- `dengue_flush_score`: Float

## VisualBiomarkerResult
- `color_biomarkers`: ColorBiomarkers
- `classifier_scores`: Dict[String, Float] (MobileNetV3 multi-task outputs)
- `uncertainty_flags`: List[String] (e.g. "Lighting too dim for reliable cyanosis detection")

## SenseResult (Fusion Output - Layer 1 → Layer 2 Contract)
- `disease_probabilities`: Dict[String, Float] (Probabilities for 12 target diseases)
- `rppg`: VitalsResult
- `audio`: AudioAnalysisResult
- `visual`: VisualBiomarkerResult
- `uncertainty`: Dict[String, Tuple[Float, Float]] (Lower and upper confidence bounds per disease)
- `processing_time_ms`: Integer
