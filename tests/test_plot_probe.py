"""Tests for duplicate-gated plot probe and redo suggestions."""

from __future__ import annotations

import copy

from uqlab_orchestrator.config import TRAINING_CONFIG, default_workflow
from uqlab_orchestrator.plot_probe import (
    PlotProbeResult,
    assess_outcome,
    biased_nudge,
    suggest_sample_size_patch,
    suggest_workflow_patch,
)
from uqlab_orchestrator.plot_probe.duplicate_gate import (
    DuplicateGroup,
    assess_duplicate_outcome,
    find_duplicate_groups,
)
from uqlab_orchestrator.plot_probe.outcome import (
    FAIL_INSUFFICIENT_RUNS,
    FAIL_MISSING_ARTIFACTS,
)
from uqlab_orchestrator.plot_probe.suggest import TunableKnob


def test_training_config_quick_epochs_above_two():
    assert TRAINING_CONFIG["quick"]["epochs"] > 2


def test_default_workflow_epochs_above_two():
    wf = default_workflow()
    assert int(wf["training_config"]["epochs"]) > 2


def test_assess_outcome_missing_artifacts():
    probe = assess_outcome([])
    assert not probe.ok
    assert probe.failure_kind == FAIL_MISSING_ARTIFACTS


def test_assess_outcome_insufficient_runs():
    experiments = [
        {"id": "a", "status": "completed", "results_path": None},
    ]
    probe = assess_outcome(experiments)
    assert not probe.ok
    assert probe.failure_kind in (FAIL_MISSING_ARTIFACTS, FAIL_INSUFFICIENT_RUNS)


def test_suggest_workflow_patch_increases_epochs():
    wf = default_workflow()
    before_epochs = int(wf["training_config"]["epochs"])
    probe = PlotProbeResult.fail(
        stage="viz",
        failure_kind="build_error",
        message="plot failed",
    )
    suggestion = suggest_workflow_patch(wf, probe=probe, source_label="test-run")
    after_epochs = int(suggestion.patched_workflow["training_config"]["epochs"])
    assert after_epochs >= before_epochs
    assert suggestion.diffs


def test_biased_nudge_mostly_upward():
    knob = TunableKnob(
        "epochs",
        lambda w: 12,
        lambda w, v: None,
        step=3,
        min_val=1,
        max_val=200,
        up_bias=1.0,
    )
    import random

    rng = random.Random(0)
    assert biased_nudge(12, knob, rng) == 15


def test_find_duplicate_groups_empty_inputs():
    assert find_duplicate_groups([], []) == []
    assert find_duplicate_groups([{"data": {}}], []) == []


def test_assess_duplicate_outcome_ok_has_no_suggestion():
    wf = default_workflow()
    group = DuplicateGroup(
        match_key=("k",),
        experiments=({"id": "x", "status": "completed"},),
        representative_id="x",
        representative_name="test",
    )
    from unittest.mock import patch

    ok_probe = PlotProbeResult.pass_ok(run_ids=("a", "b"), points=3)
    with patch(
        "uqlab_orchestrator.plot_probe.duplicate_gate.assess_outcome",
        return_value=ok_probe,
    ):
        outcome = assess_duplicate_outcome(group, wf)
    assert outcome.probe.ok
    assert outcome.suggestion is None
    assert outcome.sample_size_suggestion is None


def test_suggest_sample_size_patch_when_epochs_match():
    wf = default_workflow()
    wf["training_config"]["epochs"] = 12
    probe = PlotProbeResult.fail(
        stage="viz",
        failure_kind="build_error",
        message="plot failed",
    )
    dup_cfg = {"training": {"epochs": 12}, "data": {}}
    alt = suggest_sample_size_patch(
        wf,
        probe=probe,
        source_label="dup-run",
        duplicate_cfg=dup_cfg,
    )
    assert alt is not None
    assert alt.variant == "sample_size"
    assert alt.diffs
    uc = alt.patched_workflow["uncertainty_config"]
    ev = alt.patched_workflow["evaluation_config"]
    assert int(uc["regular_train_per_class"]) > 300
    assert int(ev["eval_per_group"]) > 100
    assert alt.pool_note


def test_suggest_sample_size_patch_skips_when_epochs_differ():
    wf = default_workflow()
    wf["training_config"]["epochs"] = 15
    probe = PlotProbeResult.fail(
        stage="viz",
        failure_kind="build_error",
        message="plot failed",
    )
    dup_cfg = {"training": {"epochs": 12}}
    assert (
        suggest_sample_size_patch(
            wf,
            probe=probe,
            duplicate_cfg=dup_cfg,
        )
        is None
    )


def test_propose_sample_size_targets_respects_pool_at_cap():
    from uqlab_orchestrator.plot_probe.dataset_pool import propose_sample_size_targets

    wf = default_workflow()
    wf["uncertainty_config"]["regular_train_per_class"] = 5000
    wf["uncertainty_config"]["under_train_per_class"] = 4999
    wf["evaluation_config"]["eval_per_group"] = 2000
    assert propose_sample_size_targets(wf) is None


def test_biased_nudge_upward_majority():
    import random

    knob = TunableKnob(
        "epochs",
        lambda w: 12,
        lambda w, v: None,
        step=3,
        min_val=1,
        max_val=200,
        up_bias=0.75,
    )
    rng = random.Random(42)
    ups = sum(1 for _ in range(200) if biased_nudge(12, knob, rng) > 12)
    assert ups >= 120
