"""
PRISM SENSE Pipeline Profiler.
Measures per-component latency and identifies bottlenecks.
"""
import time
import os
import sys
import numpy as np
import torch

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def profile_fusion(n_runs: int = 100):
    """Profile fusion model inference latency."""
    from layer1_sense.fusion.cross_modal_fusion import PRISMFusionModel

    model = PRISMFusionModel()
    model.eval()

    rppg = torch.randn(1, 7)
    audio = torch.randn(1, 16)
    visual = torch.randn(1, 11)

    # Warmup
    for _ in range(10):
        with torch.no_grad():
            model(rppg, audio, visual)

    latencies = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        with torch.no_grad():
            model(rppg, audio, visual)
        latencies.append((time.perf_counter() - t0) * 1000)

    lat = np.array(latencies)
    print(f"\n--- Fusion Model ---")
    print(f"  Mean: {lat.mean():.2f} ms  (target < 10 ms)")
    print(f"  P95:  {np.percentile(lat, 95):.2f} ms")
    return lat.mean()

def profile_rppg_signal(n_runs: int = 100):
    """Profile rPPG signal processing (CHROM + Welch)."""
    from layer1_sense.rppg.signal_processor import PRISMrPPGProcessor
    from layer1_sense.rppg.vitals_estimator import PRISMVitalsEstimator

    proc = PRISMrPPGProcessor(fps=30)
    est = PRISMVitalsEstimator(fps=30)

    rgb = np.random.randn(900, 3)  # 30s @ 30fps

    latencies = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        bvp = proc.chrom_method(rgb)
        bvp = proc.bandpass_filter(bvp)
        hr = est.estimate_hr(bvp)
        latencies.append((time.perf_counter() - t0) * 1000)

    lat = np.array(latencies)
    print(f"\n--- rPPG Signal Processing ---")
    print(f"  Mean: {lat.mean():.2f} ms  (target < 100 ms)")
    print(f"  P95:  {np.percentile(lat, 95):.2f} ms")
    return lat.mean()

def profile_cough_detector(n_runs: int = 100):
    """Profile cough detection on 5s audio."""
    from layer1_sense.audio.cough_detector import PRISMCoughDetector

    det = PRISMCoughDetector(sample_rate=16000)
    audio = np.random.randn(16000 * 5).astype(np.float32)

    latencies = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        det.detect_coughs(audio)
        latencies.append((time.perf_counter() - t0) * 1000)

    lat = np.array(latencies)
    print(f"\n--- Cough Detection ---")
    print(f"  Mean: {lat.mean():.2f} ms  (target < 50 ms)")
    print(f"  P95:  {np.percentile(lat, 95):.2f} ms")
    return lat.mean()

def profile_visual_classifier(n_runs: int = 50):
    """Profile MobileNetV3 visual classifier."""
    from layer1_sense.visual.disease_classifier import PRISMVisualClassifier

    clf = PRISMVisualClassifier(pretrained=False)
    frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)

    # Warmup
    for _ in range(5):
        clf.predict(frame)

    latencies = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        clf.predict(frame)
        latencies.append((time.perf_counter() - t0) * 1000)

    lat = np.array(latencies)
    print(f"\n--- Visual Classifier ---")
    print(f"  Mean: {lat.mean():.2f} ms  (target < 30 ms)")
    print(f"  P95:  {np.percentile(lat, 95):.2f} ms")
    return lat.mean()

def audit_model_sizes():
    """T047: Verify combined TFLite/ONNX model sizes < 15MB."""
    models_dir = "android_integration/models"
    total = 0.0

    print(f"\n--- Model Size Audit ---")
    for f in sorted(os.listdir(models_dir)):
        path = os.path.join(models_dir, f)
        if os.path.isfile(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            total += size_mb
            print(f"  {f}: {size_mb:.3f} MB")

    print(f"  TOTAL: {total:.3f} MB  (target < 15 MB)")
    status = "PASS" if total < 15.0 else "FAIL"
    print(f"  Status: {status}")
    return total

if __name__ == "__main__":
    print("=== PRISM SENSE Pipeline Profiler ===")

    fusion_ms = profile_fusion()
    rppg_ms = profile_rppg_signal()
    cough_ms = profile_cough_detector()
    visual_ms = profile_visual_classifier()

    total_size = audit_model_sizes()

    print(f"\n=== Summary ===")
    targets = [
        ("Fusion", fusion_ms, 10),
        ("rPPG Signal", rppg_ms, 100),
        ("Cough Detection", cough_ms, 50),
        ("Visual Classifier", visual_ms, 30),
    ]
    all_pass = True
    for name, actual, target in targets:
        status = "PASS" if actual < target else "WARN"
        if status == "WARN":
            all_pass = False
        print(f"  {name}: {actual:.1f}ms / {target}ms [{status}]")

    size_pass = total_size < 15.0
    print(f"  Model Size: {total_size:.2f}MB / 15MB [{'PASS' if size_pass else 'FAIL'}]")
    print(f"\nOverall: {'ALL TARGETS MET' if all_pass and size_pass else 'SOME TARGETS EXCEEDED'}")
