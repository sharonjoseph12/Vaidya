# Android Integration Contract

This contract defines the API boundaries for the Layer 1 SENSE module when integrated into the PRISM Android application.

## PRISMSenseModule (Kotlin Interface)

The Android team (Person 4) will expect the following interfaces from the compiled Layer 1 artifacts (TFLite models + wrapper code):

```kotlin
interface PRISMSenseModule {
    
    /**
     * Initializes the module by loading all TFLite models into memory.
     * @param context Application context.
     * @param modelDir Directory containing the exported .tflite files.
     */
    fun initialize(context: Context, modelDir: String)

    /**
     * Runs rPPG and Visual biomarker analysis on a recorded video file.
     * @param videoPath Absolute path to the recorded MP4 file (minimum 30 seconds).
     * @return Pair containing the VitalsResult and VisualBiomarkerResult.
     */
    suspend fun analyzeVideo(videoPath: String): Pair<VitalsResult, VisualBiomarkerResult>

    /**
     * Runs acoustic biomarker analysis on a recorded audio file.
     * @param audioPath Absolute path to the recorded WAV/M4A file.
     * @return AudioAnalysisResult containing cough, breathing, and voice features.
     */
    suspend fun analyzeAudio(audioPath: String): AudioAnalysisResult

    /**
     * Fuses the results from individual modalities into a final set of disease probabilities.
     * @param rppgResult Result from video analysis.
     * @param audioResult Result from audio analysis.
     * @param visualResult Result from visual analysis.
     * @return SenseResult containing fused probabilities and uncertainty bounds.
     */
    suspend fun fuseResults(
        rppgResult: VitalsResult,
        audioResult: AudioAnalysisResult,
        visualResult: VisualBiomarkerResult
    ): SenseResult

    /**
     * (Optional) Processes camera frames in real-time for immediate user feedback.
     * @param cameraFrames Flow of Bitmaps from Android CameraX.
     * @return Flow of partial updates (e.g. current HR estimate, face detection status).
     */
    fun analyzeRealtime(cameraFrames: Flow<Bitmap>): Flow<PartialResult>
}
```

## Required Assets
The module requires the following exported models to be placed in the `modelDir`:
1. `cough_classifier.tflite` (FP16 quantized)
2. `rppg_processor.tflite` (FP16/FP32)
3. `visual_classifier.tflite` (FP16 quantized)
4. `fusion_model.tflite` (INT8 quantized)
