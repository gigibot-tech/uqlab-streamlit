"""
Backward compatibility layer for benchmarks module.
All functionality has been moved to 4_evaluation/benchmarks/.
"""
import warnings

warnings.warn(
    "Importing from 'benchmarks' is deprecated. "
    "Please update imports to: from walaris.4_evaluation.benchmarks import ...",
    DeprecationWarning,
    stacklevel=2
)

from ..4_evaluation.benchmarks import *
