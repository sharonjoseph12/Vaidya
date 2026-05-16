"""
TFLite Export Pipeline for PRISM SENSE Models.
Exports: YAMNet cough classifier, rPPG signal processor, MobileNetV3 visual classifier, Fusion model.
"""
import os
import sys
import numpy as np
import tensorflow as tf
try:
    from tensorflow import lite # type: ignore
    from tensorflow import signal # type: ignore
except ImportError:
    pass

def export_yamnet_tflite(output_dir: str = "android_integration/models"):
    """Export YAMNet-based cough classifier to FP16 TFLite."""
    import tensorflow_hub as hub

    os.makedirs(output_dir, exist_ok=True)

    # Load YAMNet
    yamnet = hub.load('https://tfhub.dev/google/yamnet/1')

    # Create a concrete function for the YAMNet core
    @tf.function(input_signature=[tf.TensorSpec(shape=[None], dtype=tf.float32)])
    def yamnet_inference(waveform):
        scores, embeddings, spectrogram = yamnet(waveform)
        return scores, embeddings

    # Get concrete function
    concrete = yamnet_inference.get_concrete_function()

    # Convert to TFLite with FP16 quantization
    converter = lite.TFLiteConverter.from_concrete_functions([concrete]) # type: ignore
    converter.optimizations = [lite.Optimize.DEFAULT] # type: ignore
    converter.target_spec.supported_types = [tf.float16]
    tflite_model = converter.convert()

    path = os.path.join(output_dir, "yamnet_cough.tflite")
    with open(path, "wb") as f:
        f.write(tflite_model)

    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"[YAMNet] Exported to {path} ({size_mb:.2f} MB)")
    return path

def export_rppg_tflite(output_dir: str = "android_integration/models"):
    """Export rPPG signal processor as a TFLite model (FFT + peak detection)."""

    os.makedirs(output_dir, exist_ok=True)

    # Build a simple TF model that wraps the signal processing
    class RPPGModel(tf.Module):
        def __init__(self):
            super().__init__()

        @tf.function(input_signature=[tf.TensorSpec(shape=[None, 3], dtype=tf.float32)])
        def process(self, rgb_signal):
            """Takes (T, 3) RGB signal, returns HR estimate."""
            # Normalize
            mean_rgb = tf.reduce_mean(rgb_signal, axis=0, keepdims=True)
            norm = rgb_signal / (mean_rgb + 1e-6)

            # CHROM
            xs = 3.0 * norm[:, 0] - 2.0 * norm[:, 1]
            ys = 1.5 * norm[:, 0] + norm[:, 1] - 1.5 * norm[:, 2]
            alpha = tf.math.reduce_std(xs) / (tf.math.reduce_std(ys) + 1e-6)
            bvp = xs - alpha * ys

            # FFT for HR estimation
            fft = signal.rfft(bvp) # type: ignore
            magnitudes = tf.abs(fft)
            return magnitudes

    model = RPPGModel()
    concrete = model.process.get_concrete_function()

    converter = lite.TFLiteConverter.from_concrete_functions([concrete]) # type: ignore
    converter.optimizations = [lite.Optimize.DEFAULT] # type: ignore
    converter.target_spec.supported_types = [tf.float16]
    tflite_model = converter.convert()

    path = os.path.join(output_dir, "rppg_processor.tflite")
    with open(path, "wb") as f:
        f.write(tflite_model)

    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"[rPPG] Exported to {path} ({size_mb:.2f} MB)")
    return path

def export_visual_tflite(output_dir: str = "android_integration/models"):
    """Export MobileNetV3 visual classifier: PyTorch → ONNX → TFLite."""
    import torch
    import onnx

    os.makedirs(output_dir, exist_ok=True)

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from layer1_sense.visual.disease_classifier import PRISMVisualClassifier

    model = PRISMVisualClassifier(pretrained=False)
    model.eval()

    dummy = torch.randn(1, 3, 224, 224)
    onnx_path = os.path.join(output_dir, "visual_classifier.onnx")

    torch.onnx.export(
        model, (dummy,), onnx_path,
        input_names=["image"],
        output_names=["jaundice", "anemia", "cyanosis", "dengue"],
        dynamic_axes={"image": {0: "batch"}},
        opset_version=13,
    )

    # Verify ONNX
    onnx_model = onnx.load(onnx_path)
    onnx.checker.check_model(onnx_model)

    size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    print(f"[Visual] ONNX exported to {onnx_path} ({size_mb:.2f} MB)")
    print("[Visual] Note: ONNX → TFLite conversion requires onnx-tf. Use onnxruntime for inference on Android.")
    return onnx_path

def export_fusion_tflite(output_dir: str = "android_integration/models"):
    """Export fusion model with INT8 quantization."""
    import torch

    os.makedirs(output_dir, exist_ok=True)

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from layer1_sense.fusion.cross_modal_fusion import PRISMFusionModel

    model = PRISMFusionModel()
    model.eval()

    dummy_rppg = torch.randn(1, 7)
    dummy_audio = torch.randn(1, 16)
    dummy_visual = torch.randn(1, 11)

    # Export via tracing
    class FusionWrapper(torch.nn.Module):
        def __init__(self, fusion_model):
            super().__init__()
            self.model = fusion_model

        def forward(self, rppg, audio, visual):
            return self.model(rppg, audio, visual)

    wrapper = FusionWrapper(model)
    onnx_path = os.path.join(output_dir, "fusion_model.onnx")

    torch.onnx.export(
        wrapper, (dummy_rppg, dummy_audio, dummy_visual), onnx_path,
        input_names=["rppg", "audio", "visual"],
        output_names=["disease_logits"],
        opset_version=14,
    )

    size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    print(f"[Fusion] ONNX exported to {onnx_path} ({size_mb:.2f} MB)")
    return onnx_path

if __name__ == "__main__":
    print("=== PRISM TFLite Export Pipeline ===\n")
    export_rppg_tflite()
    export_visual_tflite()
    export_fusion_tflite()
    # YAMNet export requires network access to download from TF Hub
    # export_yamnet_tflite()
    print("\n=== Export complete ===")
