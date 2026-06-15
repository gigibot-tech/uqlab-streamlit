"""
UQ Methods Module

Implements various uncertainty quantification methods:
- Gaussian Logits: Two-head architecture for disentangled uncertainty
- Information-Theoretic: MI/EE/PE decomposition (TODO)
- DualXDA Adapter: Wraps existing DualXDA implementation (TODO)
"""

from walaris.benchmarks.models.base import UQMethod, KerasUQMethod, PyTorchUQMethod

try:
    from walaris.benchmarks.models.gaussian_logits import GaussianLogitsMethod, create_gaussian_logits_method
    GAUSSIAN_LOGITS_AVAILABLE = True
except ImportError:
    GAUSSIAN_LOGITS_AVAILABLE = False
    GaussianLogitsMethod = None
    create_gaussian_logits_method = None

__all__ = [
    "UQMethod",
    "KerasUQMethod",
    "PyTorchUQMethod",
    "GaussianLogitsMethod",
    "create_gaussian_logits_method",
    "GAUSSIAN_LOGITS_AVAILABLE",
]

# Made with Bob
