"""Tests for ExperimentDisentanglingModel and vendored json_results_to_df."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import numpy as np
import torch

from uqlab.evaluation.benchmarks.disentangling import (
    ExperimentDisentanglingModel,
    UQLabDisentanglingBridge,
    json_results_to_df,
)
from uqlab.evaluation.benchmarks.disentangling.experiment import resolve_disentangling_signal_pair
from uqlab.vendor.disentanglement_error.util import Config, CustomJsonEncoder, ExperimentResults, RunResults


def _write_results_pt(run_dir: Path, n: int = 20) -> None:
    torch.save(
        {
            "signal_table": {
                "expected_entropy": torch.linspace(0.3, 0.7, n),
                "mutual_info": torch.linspace(0.1, 0.5, n),
                "inverse_coherence": torch.linspace(0.2, 0.8, n),
                "inverse_mass": torch.linspace(0.1, 0.9, n),
            },
            "predictions": torch.randint(0, 10, (n,)),
            "eval_clean_labels": torch.zeros(n, dtype=torch.long),
        },
        run_dir / "results.pt",
    )


def test_paper_mode_defaults():
    model = ExperimentDisentanglingModel()
    assert model.aleatoric_signal == "expected_entropy"
    assert model.epistemic_signal == "mutual_info"
    assert UQLabDisentanglingBridge is ExperimentDisentanglingModel


def test_signal_mode_preset():
    model = ExperimentDisentanglingModel(predict_mode="signal")
    assert model.aleatoric_signal == "inverse_coherence_dualxda"
    assert model.epistemic_signal == "inverse_mass_dualxda"


def test_signal_ek_fak_mode_preset():
    model = ExperimentDisentanglingModel(predict_mode="signal_ek_fak")
    assert model.aleatoric_signal == "inverse_coherence_ek_fak"
    assert model.epistemic_signal == "inverse_mass_ek_fak"


def test_explicit_kwargs_override_predict_mode():
    model = ExperimentDisentanglingModel(
        predict_mode="paper",
        aleatoric_signal="inverse_coherence",
        epistemic_signal="inverse_mass",
    )
    assert model.aleatoric_signal == "inverse_coherence_dualxda"
    assert model.epistemic_signal == "inverse_mass_dualxda"


def test_workflow_uncertainty_config_pairing():
    workflow = {
        "uncertainty_config": {
            "aleatoric_signal": "inverse_coherence",
            "epistemic_signal": "inverse_dominance",
        }
    }
    alea, epi = resolve_disentangling_signal_pair(workflow=workflow)
    assert alea == "inverse_coherence_dualxda"
    assert epi == "inverse_dominance_dualxda"


def test_explicit_kwargs_beat_workflow():
    workflow = {
        "uncertainty_config": {
            "aleatoric_signal": "inverse_coherence",
            "epistemic_signal": "inverse_dominance",
        }
    }
    alea, epi = resolve_disentangling_signal_pair(
        workflow=workflow,
        aleatoric_signal="expected_entropy",
        epistemic_signal="mutual_info",
    )
    assert alea == "expected_entropy"
    assert epi == "mutual_info"


def test_predict_disentangling_reads_results_pt(tmp_path):
    run_dir = tmp_path / "run_0000"
    run_dir.mkdir()
    _write_results_pt(run_dir, n=15)

    model = ExperimentDisentanglingModel(results_dir=run_dir)

    pred, alea, epi = model.predict_disentangling(np.zeros((15, 1)))

    assert pred.shape == (15,)
    assert alea.shape == (15,)
    assert epi.shape == (15,)


import pytest


def test_fit_legacy_mode_raises():
    model = ExperimentDisentanglingModel()
    with pytest.raises(NotImplementedError):
        model.fit(np.zeros((10, 1)), np.zeros(10), label_noise=0.25)


def test_json_results_to_df_rows():
    results = RunResults(
        label_noise_results=[ExperimentResults(scores=[0.9], aleatorics=[0.3], epistemics=[0.7])],
        decreasing_dataset_results=[ExperimentResults(scores=[0.8], aleatorics=[0.4], epistemics=[0.6])],
    )
    config = Config(label_noises=[0.0], dataset_sizes=[0.5], n_runs=1)

    df = json_results_to_df(
        json.dumps(results, cls=CustomJsonEncoder),
        json.dumps(config, cls=CustomJsonEncoder),
    )

    assert len(df) == 2
    assert set(df["Experiment"]) == {"Label Noise", "Decreasing Dataset"}
