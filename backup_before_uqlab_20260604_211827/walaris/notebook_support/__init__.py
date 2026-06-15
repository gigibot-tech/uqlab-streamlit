"""
Backward compatibility layer for notebook_support module.
All functionality has been moved to shared/notebook_utils/.
"""
import warnings

warnings.warn(
    "Importing from 'notebook_support' is deprecated. "
    "Please update imports to: from walaris.shared.notebook_utils import ...",
    DeprecationWarning,
    stacklevel=2
)

from ..shared.notebook_utils import *
from ..shared.notebook_utils.comparisons import *
