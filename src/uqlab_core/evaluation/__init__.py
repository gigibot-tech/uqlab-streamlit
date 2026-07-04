"""Evaluation — start with :func:`run_uncertainty_eval`."""

from __future__ import annotations

_LAZY = {
    "EvalSignalConfig": ("uqlab_core.runner.config", "EvalSignalConfig"),
    "UncertaintyEvalResult": ("uqlab_core.evaluation.pipeline", "UncertaintyEvalResult"),
    "collect_uncertainty_signals": ("uqlab_core.evaluation.pipeline", "collect_uncertainty_signals"),
    "run_uncertainty_eval": ("uqlab_core.evaluation.pipeline", "run_uncertainty_eval"),
    "score_uncertainty_signals": ("uqlab_core.evaluation.pipeline", "score_uncertainty_signals"),
}

__all__ = list(_LAZY.keys())


def __getattr__(name: str):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    mod_name, attr = spec
    from importlib import import_module

    return getattr(import_module(mod_name), attr)
