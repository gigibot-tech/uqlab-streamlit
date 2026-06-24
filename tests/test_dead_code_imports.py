"""Smoke tests after dead_code archive moves."""

from __future__ import annotations


def test_core_evaluation_imports():
    from uqlab.evaluation.metrics import binary_auroc
    from uqlab.evaluation.legacy.triage.dualxda_axioms import DualXDATracer

    assert callable(binary_auroc)
    assert DualXDATracer is not None


def test_disentangling_public_api():
    from uqlab.evaluation.benchmarks.disentangling import (
        DisentanglingModel,
        ExperimentDisentanglingModel,
        calculate_disentanglement_error,
        json_results_to_df,
    )

    assert issubclass(ExperimentDisentanglingModel, DisentanglingModel)
    assert callable(calculate_disentanglement_error)
    assert callable(json_results_to_df)


def test_vendor_package_imports():
    from uqlab.vendor.disentanglement_error import Config, calculate_disentanglement_error

    cfg = Config(n_runs=1)
    assert cfg.n_runs == 1
    assert callable(calculate_disentanglement_error)
