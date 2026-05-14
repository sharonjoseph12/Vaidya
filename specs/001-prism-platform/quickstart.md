# PRISM Layer 1 (SENSE) Quickstart

## Installation

1. Create a Python 3.11 virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install the exact required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure your `requirements.txt` contains `mediapipe==0.10.9`, `opencv-python==4.9.0.80`, `torch==2.1.2`, `torchaudio==2.1.2`, `librosa==0.10.1`, `tensorflow==2.15.0`, etc. as specified in the plan)*

3. (Optional) Install `praat-parselmouth` and `pyAudioAnalysis` for advanced voice biomarker extraction:
   ```bash
   pip install praat-parselmouth pyAudioAnalysis
   ```

## Running the Pipeline

To run a basic end-to-end extraction on sample files:

```python
from layer1_sense.fusion.cross_modal_fusion import PRISMFusionModel
from layer1_sense.audio.audio_pipeline import PRISMAudioPipeline
from layer1_sense.rppg.rppg_pipeline import PRISMrPPGPipeline
from layer1_sense.visual.visual_pipeline import PRISMVisualPipeline

# Initialize pipelines
audio_pipe = PRISMAudioPipeline()
rppg_pipe = PRISMrPPGPipeline()
visual_pipe = PRISMVisualPipeline()
fusion = PRISMFusionModel()

# Process data
audio_res = audio_pipe.full_analysis("sample_audio.wav")
rppg_res = rppg_pipe.process_video("sample_video.mp4")
visual_res = visual_pipe.analyze_video("sample_video.mp4")

# Fuse (assuming proper tensor conversion methods exist)
probs, uncertainty = fusion(audio_res, visual_res, rppg_res)
print(probs)
```

## Running Tests

To verify your environment is correctly configured:

```bash
pytest layer1_sense/tests/
```
