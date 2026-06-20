"""Tests for EK-FAK signal validation, registry, and pipeline wiring."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import torch

from uqlab.evaluation.signals.attribution import build_fast_pilot_signal_table
from uqlab.evaluation.signals.primitives import ATTR_COHERENCE
from uqlab.evaluation.signals.registry import (
    METRICS,
    build_signal_table_from_store,
    legacy_store_from_kwargs,
    predicted_class_logit_magnitude,
    signals_from_flat_list,
)
from uqlab.evaluation.signals.sources import (
    ATTRIBUTION_METHODS,
    EvalContext,
    sources_for_metrics,
)
from uqlab.models.architecture import normalize_architecture, scope_to_training_mode
from uqlab.shared.config.signals import (
    DEFAULT_SIGNALS,
    flatten_signals,
    prune_signals_for_runtime,
    validate_evaluation_signals,
)
from uqlab_orchestrator.run_spec import build_run_yaml


def _attr_raw(n: int) -> dict:
    return {
        "coherence": torch.ones(n) * 0.5,
        "mass": torch.ones(n),
        "dominance": torch.ones(n) * 0.2,
        "label_disagreement": torch.zeros(n),
        "noisy_support_ratio": torch.zeros(n),
        "attribution_concentration": torch.zeros(n),
        "cross_class_support": torch.zeros(n),
        "inverse_coherence": torch.ones(n) * 0.5,
    }


def _mc_uq(n: int, mean_pred: torch.Tensor | None = None) -> dict:
    if mean_pred is None:
        mean_pred = torch.softmax(torch.ones(n, 10), dim=1)
    return {
        "mean_prediction": mean_pred,
        "entropy": torch.zeros(n),
        "mutual_info": torch.zeros(n),
    }


def test_normalize_architecture_aliases():
    assert normalize_architecture("resnet18_mcdropout") == "resnet18"
    assert normalize_architecture("resnet18") == "resnet18"
    assert normalize_architecture("cnn_mcdropout") == "cnn_small"


def test_mutual_info_requires_mc_and_dropout():
    with pytest.raises(ValueError, match="mc_passes"):
        validate_evaluation_signals(
            signals=DEFAULT_SIGNALS,
            mc_passes=0,
            dropout=0.1,
        )


def test_scope_mapping():
    assert scope_to_training_mode("resnet18", "full") == "end_to_end"
    assert scope_to_training_mode("resnet18", "head_only") == "feature_space"


def test_inverse_logit_magnitude_uses_predicted_class_logit():
    det_logits = torch.tensor([[3.0, 1.0, 0.5], [0.2, 4.0, 0.1]])
    mean_pred = torch.softmax(det_logits, dim=1)
    mag = predicted_class_logit_magnitude(det_logits, mean_pred)
    assert mag[0].item() == pytest.approx(3.0)
    assert mag[1].item() == pytest.approx(4.0)

    store = legacy_store_from_kwargs(
        attribution_signals=_attr_raw(2),
        det_logits=det_logits,
        mean_pred_det=mean_pred,
        mc_uq=_mc_uq(2, mean_pred),
    )
    table = build_signal_table_from_store(store, enabled={"inverse_logit_magnitude"})
    expected = 1.0 / (mag + 1e-8)
    assert torch.allclose(table["inverse_logit_magnitude"], expected)


def test_inverse_dominance_is_one_minus_raw_dominance():
    dom = torch.tensor([0.1, 0.9, 0.5])
    raw = _attr_raw(3)
    raw["dominance"] = dom
    store = legacy_store_from_kwargs(
        attribution_signals=raw,
        det_logits=torch.zeros(3, 10),
        mean_pred_det=torch.softmax(torch.randn(3, 10), dim=1),
        mc_uq=_mc_uq(3),
    )
    table = build_signal_table_from_store(store, enabled={"inverse_dominance"})
    assert torch.allclose(table["inverse_dominance"], 1.0 - dom)


def test_mutual_info_pruned_when_dropout_zero():
    pruned = prune_signals_for_runtime(DEFAULT_SIGNALS, mc_passes=10, dropout=0.0)
    assert "mutual_info" not in pruned["predictive"]

    n = 4
    store = legacy_store_from_kwargs(
        attribution_signals=_attr_raw(n),
        det_logits=torch.ones(n, 10),
        mean_pred_det=torch.softmax(torch.ones(n, 10), dim=1),
        mc_uq=_mc_uq(n),
    )
    table = build_signal_table_from_store(
        store, enabled=set(flatten_signals(pruned)), mc_passes=10, dropout=0.0
    )
    assert "mutual_info" not in table


def test_selected_signals_round_trip_into_yaml():
    workflow = {
        "dataset_config": {
            "dataset_name": "cifar10",
            "noise_type": "clean_label",
            "stats": {"noise_rate": 0.0},
        },
        "training_config": {
            "model_architecture": "resnet18",
            "epochs": 12,
            "dropout": 0.0,
            "hidden_dim": 256,
            "learning_rate": 0.001,
            "batch_size": 256,
        },
        "uncertainty_config": {
            "epistemic_enabled": False,
            "regular_train_per_class": 300,
            "aleatoric_enabled": True,
        },
        "evaluation_config": {
            "eval_per_group": 100,
            "mc_passes": 10,
            "selected_signals": ["msp_uncertainty", "inverse_mass", "inverse_coherence"],
        },
    }
    cfg = build_run_yaml(workflow)
    flat = flatten_signals(cfg["evaluation"]["signals"])
    assert flat == ["msp_uncertainty", "inverse_coherence", "inverse_mass"]


def test_signals_from_flat_list_aliases_dominance():
    families = signals_from_flat_list(["dominance", "msp_uncertainty"])
    assert families["attribution"] == ["inverse_dominance"]
    assert families["predictive"] == ["msp_uncertainty"]


def test_enabled_subset_filters_exported_columns():
    n = 3
    store = legacy_store_from_kwargs(
        attribution_signals=_attr_raw(n),
        det_logits=torch.ones(n, 10),
        mean_pred_det=torch.softmax(torch.ones(n, 10), dim=1),
        mc_uq=_mc_uq(n),
    )
    table = build_signal_table_from_store(
        store, enabled={"msp_uncertainty", "inverse_mass"}, mc_passes=10, dropout=0.0
    )
    assert set(table.keys()) == {"msp_uncertainty", "inverse_mass"}
    assert len(METRICS) == 7


def test_sources_for_metrics_skips_attribution_when_not_needed():
    needed = sources_for_metrics({"msp_uncertainty", "inverse_logit_magnitude"})
    assert needed == {"mc_dropout", "deterministic_forward"}
    assert "attribution" not in needed


def test_mock_attribution_method_feeds_inverse_coherence():
    n = 5
    coherence = torch.linspace(0.1, 0.9, n)

    def mock_primitives(ctx: EvalContext):
        return {
            ATTR_COHERENCE: coherence,
            "attribution.mass": torch.ones(n),
            "attribution.dominance": torch.zeros(n),
        }

    original = ATTRIBUTION_METHODS.get("dualxda")
    ATTRIBUTION_METHODS["mock"] = mock_primitives
    try:
        store = mock_primitives(
            EvalContext(
                model=MagicMock(),
                train_dataset=MagicMock(),
                eval_inputs=torch.zeros(n, 3),
                eval_x=torch.zeros(n, 3),
                device=torch.device("cpu"),
                train_batch_size=2,
                top_k=2,
                mc_passes=1,
                dropout=0.0,
                attribution_method="mock",
                run_cache_dir=MagicMock(),
            )
        )
        table = build_signal_table_from_store(store, enabled={"inverse_coherence"})
        assert torch.allclose(table["inverse_coherence"], 1.0 - coherence)
    finally:
        if original is not None:
            ATTRIBUTION_METHODS["dualxda"] = original
        ATTRIBUTION_METHODS.pop("mock", None)


def test_signal_calculator_archived():
    with pytest.raises(ImportError, match="archive/legacy_src"):
        from uqlab.evaluation.signals import SignalCalculator  # noqa: F401


def test_build_fast_pilot_signal_table_legacy_path():
    n = 8
    raw = _attr_raw(n)
    mean_pred = torch.softmax(torch.randn(n, 10), dim=1)
    table = build_fast_pilot_signal_table(
        attribution_signals=raw,
        det_logits=torch.randn(n, 10),
        mean_pred_det=mean_pred,
        mc_uq=_mc_uq(n, mean_pred),
        enabled={"inverse_coherence"},
    )
    assert "inverse_coherence" in table
