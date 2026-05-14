package com.prism

import android.media.Image

class VideoAnalyzer {
    fun processFrame(image: Image): FloatArray {
        // Run CameraX frame through MediaPipe face mesh
        // Extract rPPG signal, perform visual biomarker TFLite inference
        return floatArrayOf(0.5f, 0.2f) // Stub output
    }
}
