"""
PRISM core ML artifact loaders (finetuned weights in ``core_ml/``).

Implementation lives in ``artifact_runtime.py``; this module re-exports stable names.
"""

from backend.core_ml.artifact_runtime import (  # noqa: F401
    MockModel,
    clear_ml_runtime_cache,
    load_yamnet_runtime,
    load_trajectory_runtime,
    load_causal_runtime,
    ml_stack_status,
)


def load_yamnet_model():
    return load_yamnet_runtime()


def load_trajectory_model():
    return load_trajectory_runtime()


def load_causal_explainer():
    return load_causal_runtime()


def load_rl_optimizer():
    return MockModel("RLOptimizer", "mock_rl_agent")
