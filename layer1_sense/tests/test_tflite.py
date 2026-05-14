"""
TFLite/ONNX validation tests — load each exported model, run inference,
verify output shapes and value ranges.
"""
import os
import pytest
import numpy as np

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "android_integration", "models")


def _skip_if_missing(path):
    if not os.path.exists(path):
        pytest.skip(f"Model not found: {path}")


class TestRPPGTFLite:
    MODEL = os.path.join(MODELS_DIR, "rppg_processor.tflite")

    def test_load_and_infer(self):
        _skip_if_missing(self.MODEL)
        import tensorflow as tf

        interpreter = tf.lite.Interpreter(model_path=self.MODEL)
        interpreter.allocate_tensors()

        inp = interpreter.get_input_details()[0]
        out = interpreter.get_output_details()[0]

        # Power-of-2 length for FFT
        data = np.random.randn(512, 3).astype(np.float32)
        interpreter.resize_tensor_input(inp["index"], data.shape)
        interpreter.allocate_tensors()

        interpreter.set_tensor(inp["index"], data)
        interpreter.invoke()
        result = interpreter.get_tensor(out["index"])

        assert result.ndim == 1
        assert len(result) == 257  # 512/2 + 1
        assert not np.isnan(result).any()


class TestVisualONNX:
    MODEL = os.path.join(MODELS_DIR, "visual_classifier.onnx")

    def test_load_and_infer(self):
        _skip_if_missing(self.MODEL)
        import onnxruntime as ort

        sess = ort.InferenceSession(self.MODEL)
        inp = np.random.randn(1, 3, 224, 224).astype(np.float32)
        outputs = sess.run(None, {"image": inp})

        # 4 heads: jaundice(4), anemia(2), cyanosis(2), dengue(2)
        assert len(outputs) == 4
        assert outputs[0].shape == (1, 4)
        assert outputs[1].shape == (1, 2)
        for o in outputs:
            assert not np.isnan(o).any()

    def test_deterministic(self):
        _skip_if_missing(self.MODEL)
        import onnxruntime as ort

        sess = ort.InferenceSession(self.MODEL)
        inp = np.ones((1, 3, 224, 224), dtype=np.float32) * 0.5
        r1 = sess.run(None, {"image": inp})
        r2 = sess.run(None, {"image": inp})
        for a, b in zip(r1, r2):
            np.testing.assert_allclose(a, b, atol=1e-5)


class TestFusionONNX:
    MODEL = os.path.join(MODELS_DIR, "fusion_model.onnx")

    def test_load_and_infer(self):
        _skip_if_missing(self.MODEL)
        import onnxruntime as ort

        sess = ort.InferenceSession(self.MODEL)
        inputs = {
            "rppg": np.random.randn(1, 7).astype(np.float32),
            "audio": np.random.randn(1, 16).astype(np.float32),
            "visual": np.random.randn(1, 11).astype(np.float32),
        }
        outputs = sess.run(None, inputs)

        assert len(outputs) == 1
        assert outputs[0].shape == (1, 12)
        assert not np.isnan(outputs[0]).any()

    def test_output_range(self):
        """Sigmoid of logits should be in [0, 1]."""
        _skip_if_missing(self.MODEL)
        import onnxruntime as ort

        sess = ort.InferenceSession(self.MODEL)
        inputs = {
            "rppg": np.random.randn(1, 7).astype(np.float32),
            "audio": np.random.randn(1, 16).astype(np.float32),
            "visual": np.random.randn(1, 11).astype(np.float32),
        }
        logits = sess.run(None, inputs)[0]
        probs = 1.0 / (1.0 + np.exp(-logits))
        assert (probs >= 0).all() and (probs <= 1).all()
