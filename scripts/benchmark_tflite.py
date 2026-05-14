"""
TFLite/ONNX Benchmark Script for PRISM SENSE Models.
Measures inference latency (mean, p95), model size, and output validity.
"""
import os
import time
import numpy as np

def benchmark_onnx(model_path: str, inputs: dict, n_runs: int = 100):
    """Benchmark an ONNX model."""
    import onnxruntime as ort

    session = ort.InferenceSession(model_path)
    latencies = []

    # Warmup
    for _ in range(5):
        session.run(None, inputs)

    for _ in range(n_runs):
        t0 = time.perf_counter()
        outputs = session.run(None, inputs)
        latencies.append((time.perf_counter() - t0) * 1000)

    latencies = np.array(latencies)
    size_mb = os.path.getsize(model_path) / (1024 * 1024)

    print(f"\n--- {os.path.basename(model_path)} ---")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Mean latency: {np.mean(latencies):.2f} ms")
    print(f"  P95 latency:  {np.percentile(latencies, 95):.2f} ms")
    print(f"  Min latency:  {np.min(latencies):.2f} ms")
    print(f"  Output shapes: {[o.shape for o in outputs]}")

    return {
        "model": os.path.basename(model_path),
        "size_mb": size_mb,
        "mean_ms": float(np.mean(latencies)),
        "p95_ms": float(np.percentile(latencies, 95)),
    }

def benchmark_tflite(model_path: str, input_data: np.ndarray, n_runs: int = 100):
    """Benchmark a TFLite model."""
    import tensorflow as tf

    interpreter = tf.lite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    # Resize input if needed
    interpreter.resize_tensor_input(input_details[0]['index'], input_data.shape)
    interpreter.allocate_tensors()

    latencies = []

    for _ in range(5):
        interpreter.set_tensor(input_details[0]['index'], input_data)
        interpreter.invoke()

    for _ in range(n_runs):
        interpreter.set_tensor(input_details[0]['index'], input_data)
        t0 = time.perf_counter()
        interpreter.invoke()
        latencies.append((time.perf_counter() - t0) * 1000)

    latencies = np.array(latencies)
    size_mb = os.path.getsize(model_path) / (1024 * 1024)

    output = interpreter.get_tensor(output_details[0]['index'])

    print(f"\n--- {os.path.basename(model_path)} ---")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Mean latency: {np.mean(latencies):.2f} ms")
    print(f"  P95 latency:  {np.percentile(latencies, 95):.2f} ms")
    print(f"  Output shape: {output.shape}")

    return {
        "model": os.path.basename(model_path),
        "size_mb": size_mb,
        "mean_ms": float(np.mean(latencies)),
        "p95_ms": float(np.percentile(latencies, 95)),
    }

def main():
    models_dir = "android_integration/models"

    print("=== PRISM Model Benchmark ===\n")
    results = []

    # rPPG TFLite
    rppg_path = os.path.join(models_dir, "rppg_processor.tflite")
    if os.path.exists(rppg_path):
        input_data = np.random.randn(1024, 3).astype(np.float32)  # Power-of-2 for FFT
        results.append(benchmark_tflite(rppg_path, input_data))

    # Visual ONNX
    visual_path = os.path.join(models_dir, "visual_classifier.onnx")
    if os.path.exists(visual_path):
        inputs = {"image": np.random.randn(1, 3, 224, 224).astype(np.float32)}
        results.append(benchmark_onnx(visual_path, inputs))

    # Fusion ONNX
    fusion_path = os.path.join(models_dir, "fusion_model.onnx")
    if os.path.exists(fusion_path):
        inputs = {
            "rppg": np.random.randn(1, 7).astype(np.float32),
            "audio": np.random.randn(1, 16).astype(np.float32),
            "visual": np.random.randn(1, 11).astype(np.float32),
        }
        results.append(benchmark_onnx(fusion_path, inputs))

    # Summary
    print("\n=== Summary ===")
    total_size = sum(r["size_mb"] for r in results)
    print(f"Total model size: {total_size:.2f} MB (target < 15 MB)")
    for r in results:
        print(f"  {r['model']}: {r['size_mb']:.2f} MB, {r['mean_ms']:.1f}ms mean")

if __name__ == "__main__":
    main()
