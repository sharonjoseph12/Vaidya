# PRISM SENSE — Android Integration Guide

## Overview

This document specifies the TFLite/ONNX model interfaces for Android integration. All models are designed for offline, on-device inference.

## Models

| Model | Format | Input Shape | Output Shape | Target Size |
|-------|--------|-------------|--------------|-------------|
| rPPG Processor | TFLite (FP16) | `(T, 3)` float32 RGB | `(T/2+1,)` FFT magnitudes | < 1 MB |
| Cough Classifier | TFLite (FP16) | `(N,)` float32 waveform @ 16kHz | `(521, 1024)` embeddings | < 5 MB |
| Visual Classifier | ONNX | `(1, 3, 224, 224)` float32 | 4 heads: jaundice(4), anemia(2), cyanosis(2), dengue(2) | < 5 MB |
| Fusion Model | ONNX | rppg:`(1,7)`, audio:`(1,16)`, visual:`(1,11)` | `(1, 12)` disease logits | < 1 MB |

**Combined target: < 15 MB**

## Kotlin Integration

### 1. rPPG Processor

```kotlin
class RPPGProcessor(context: Context) {
    private val interpreter: Interpreter

    init {
        val model = loadModelFile(context, "rppg_processor.tflite")
        interpreter = Interpreter(model)
    }

    fun process(rgbSignal: Array<FloatArray>): FloatArray {
        // rgbSignal: (T, 3) - T frames of mean RGB values
        val output = Array(1) { FloatArray(rgbSignal.size / 2 + 1) }
        interpreter.run(rgbSignal, output)
        return output[0]
    }
}
```

### 2. Visual Classifier (ONNX Runtime)

```kotlin
class VisualClassifier(context: Context) {
    private val session: OrtSession

    init {
        val env = OrtEnvironment.getEnvironment()
        session = env.createSession(
            context.assets.open("visual_classifier.onnx").readBytes()
        )
    }

    fun classify(bitmap: Bitmap): Map<String, Float> {
        val input = preprocessBitmap(bitmap, 224, 224) // CHW float32, ImageNet norm
        val tensor = OnnxTensor.createTensor(env, input)
        val results = session.run(mapOf("image" to tensor))

        return mapOf(
            "jaundice" to results["jaundice"].value,
            "anemia" to results["anemia"].value,
            "cyanosis" to results["cyanosis"].value,
            "dengue" to results["dengue"].value,
        )
    }
}
```

### 3. Fusion Model

```kotlin
class FusionInference(context: Context) {
    private val session: OrtSession

    fun predict(
        rppgFeatures: FloatArray,    // size 7
        audioFeatures: FloatArray,   // size 16
        visualFeatures: FloatArray,  // size 11
    ): FloatArray {
        val rppgTensor = OnnxTensor.createTensor(env, arrayOf(rppgFeatures))
        val audioTensor = OnnxTensor.createTensor(env, arrayOf(audioFeatures))
        val visualTensor = OnnxTensor.createTensor(env, arrayOf(visualFeatures))

        val results = session.run(mapOf(
            "rppg" to rppgTensor,
            "audio" to audioTensor,
            "visual" to visualTensor,
        ))

        // Returns 12 disease logits — apply sigmoid for probabilities
        return results["disease_logits"].value as FloatArray
    }
}
```

## Feature Vector Specifications

### rPPG Features (7 floats)
`[HR, SpO2, HRV_RMSSD, HRV_SDNN, LF_HF_Ratio, RR, HR_SNR_Confidence]`

### Audio Features (16 floats)
`[TB_prob, COVID_prob, Pneumonia_prob, Whooping_prob, Asthma_prob, COPD_prob, Healthy_prob, Uncertain_prob, breathing_rate, jitter, shimmer, HNR, cough_detected, pad, pad, pad]`

### Visual Features (11 floats)
`[jaundice_color, pallor_color, cyanosis_color, dengue_flush_color, anemia_clf, cyanosis_clf, dengue_clf, jaundice_none_clf, jaundice_mild_clf, jaundice_moderate_clf, jaundice_severe_clf]`

### Disease Output (12 classes)
`[TB, COVID, Pneumonia, Whooping_Cough, Asthma, COPD, Jaundice, Anemia, Cyanosis, Dengue, Parkinsons, Healthy]`

## Dependencies

```gradle
// build.gradle
implementation 'org.tensorflow:tensorflow-lite:2.15.0'
implementation 'com.microsoft.onnxruntime:onnxruntime-android:1.17.3'
```
