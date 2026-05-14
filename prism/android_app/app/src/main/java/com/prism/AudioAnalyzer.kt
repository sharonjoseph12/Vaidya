package com.prism

class AudioAnalyzer {
    fun processAudio(audioData: ByteArray): FloatArray {
        // Preprocess audio (e.g. resample to 22050Hz, compute mel spectrogram)
        // Feed into TFLite cough_classifier
        return floatArrayOf(0.1f, 0.9f) // Stub output
    }
}
