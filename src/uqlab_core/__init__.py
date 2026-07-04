"""uqlab_core — minimal data → train → eval pipeline."""

from __future__ import annotations

_LAZY = {
    "RunDataBundle": ("uqlab_core.data.buildData", "RunDataBundle"),
    "build_run_data": ("uqlab_core.data.buildData", "build_run_data"),
    "UncertaintyEvalResult": ("uqlab_core.evaluation.pipeline", "UncertaintyEvalResult"),
    "run_uncertainty_eval": ("uqlab_core.evaluation.pipeline", "run_uncertainty_eval"),
    "run_four_region_benchmark": ("uqlab_core.runner.notebook_run", "run_four_region_benchmark"),
    "setup_notebook": ("uqlab_core.runner.notebook_run", "setup_notebook"),
    "run_paper_experiment": ("uqlab_core.runner.train_eval", "run_paper_experiment"),
    "run_train_and_eval_phases": ("uqlab_core.runner.train_eval", "run_train_and_eval_phases"),
}

__all__ = list(_LAZY.keys())


def __getattr__(name: str):
    spec = _LAZY.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    from importlib import import_module

    mod_name, attr = spec
    return getattr(import_module(mod_name), attr)
