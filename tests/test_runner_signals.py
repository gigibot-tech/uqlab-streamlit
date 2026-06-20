"""Tests for signal validation, architecture aliases, and pipeline entry."""

from __future__ import annotations

import pytest

from uqlab.models.architecture import normalize_architecture, scope_to_training_mode
from uqlab.shared.config.signals import validate_evaluation_signals, DEFAULT_SIGNALS


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
