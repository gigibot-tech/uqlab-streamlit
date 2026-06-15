"""
UQ Benchmarks Package

A new package for uncertainty quantification benchmarking that integrates
formal disentanglement methods from research with production infrastructure.

This package provides:
- Multiple UQ methods: Gaussian Logits, Information-Theoretic, DualXDA
- Benchmark experiments: Label noise, dataset size, OOD detection
- Clean data abstractions compatible with both Keras and PyTorch
- Integration with FastAPI backend and Streamlit UI

Architecture:
- data/: Dataset loaders (CIFAR-10, Fashion-MNIST, etc.)
- models/: UQ method implementations
- benchmarks/: Formal benchmark experiments
- utils/: Helper functions and adapters
"""

__version__ = "0.1.0"

from walaris.benchmarks.datatypes import (
    Dataset,
    UqModel,
    ExperimentConfig,
    UncertaintyResults
)

__all__ = [
    "Dataset",
    "UqModel",
    "ExperimentConfig",
    "UncertaintyResults",
]

# Made with Bob
