"""Re-exports for ``uqlab.runner.phases`` compatibility."""

from uqlab_core.evaluation.pipeline import (
    collect_uncertainty_signals_core as collect_uncertainty_signals,
    score_uncertainty_signals_core as score_uncertainty_signals,
)
from uqlab_core.runner.config import (
    EvalSignalConfig,
    RunConfigView,
    apply_data_context,
    extract_run_config,
    print_experiment_configuration,
    require_complete_config,
    validate_eval_splits,
)

__all__ = [
    "EvalSignalConfig",
    "RunConfigView",
    "apply_data_context",
    "collect_uncertainty_signals",
    "extract_run_config",
    "print_experiment_configuration",
    "require_complete_config",
    "score_uncertainty_signals",
    "validate_eval_splits",
]
