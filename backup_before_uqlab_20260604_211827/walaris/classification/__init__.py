"""
Backward compatibility layer for classification module.
All functionality has been moved to the new MLOps structure.
"""
import warnings

warnings.warn(
    "Importing from 'classification' is deprecated. "
    "Please update imports to use the new structure:\n"
    "  - Models: from walaris.2_models import ...\n"
    "  - Evaluation: from walaris.4_evaluation import ...\n"
    "  - Config: from walaris.shared.config import ...\n"
    "  - Utils: from walaris.shared.utils import ...",
    DeprecationWarning,
    stacklevel=2
)

# Redirect imports
from ..2_models.classification_models import *
from ..2_models.factory import *
from ..2_models.feature_extractors import *
from ..4_evaluation.evaluator import *
from ..4_evaluation.signals.attribution import *
from ..4_evaluation.signals.formulas import *
from ..shared.config.classification import *
from ..shared.config.schemas import *
from ..shared.utils.classification import *
from ..shared.utils.tracking import *
from ..6_ui.visualization.decision_boundaries import *
from ..5_api.integrations.watsonx import *
