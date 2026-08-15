"""Tests for None-safe results markdown."""

from __future__ import annotations

import argparse
from types import SimpleNamespace

from uqlab.evaluation.reporting.result_writers import (
    _format_auroc_markdown,
    build_results_markdown,
    persist_experiment_summaries,
)


def test_format_auroc_markdown_handles_none_and_nan():
    assert _format_auroc_markdown(None) == "—"
    assert _format_auroc_markdown(float("nan")) == "—"
    assert _format_auroc_markdown(0.5263) == "0.5263"


def test_build_results_markdown_with_skipped_auroc_axes():
    split_spec = SimpleNamespace(under_supported_classes=[3, 7])
    args = argparse.Namespace(noise_type="clean_label", dinov2_model="small")
    auroc_rows = [
        ("msp_uncertainty", None, 0.4622),
        ("predictive_entropy", 0.5358, None),
        ("mutual_info", None, None),
    ]
    md = build_results_markdown(
        args=args,
        split_spec=split_spec,
        train_size=3000,
        eval_sizes={"clean": 100, "aleatoric_like": 0, "epistemic_like": 100},
        auroc_rows=auroc_rows,
        clf_rows=[("predictive_only", 0.32)],
    )
    assert "| msp_uncertainty | — | 0.4622 |" in md
    assert "| predictive_entropy | 0.5358 | — |" in md
    assert "| mutual_info | — | — |" in md


def test_persist_experiment_summaries_writes_files(tmp_path):
    split_spec = SimpleNamespace(under_supported_classes=[3, 7])
    args = argparse.Namespace(noise_type="clean_label", dinov2_model="small")
    summary = {"train_size": 100, "eval_sizes": {"clean": 0, "aleatoric_like": 100, "epistemic_like": 0}}
    persist_experiment_summaries(
        tmp_path,
        summary=summary,
        args=args,
        split_spec=split_spec,
        train_size=100,
        eval_sizes=summary["eval_sizes"],
        auroc_rows=[("msp_uncertainty", 0.5, None)],
        clf_rows=[("combined", 0.4)],
    )
    assert (tmp_path / "summary.json").exists()
    assert (tmp_path / "summary.md").exists()
    assert "—" in (tmp_path / "summary.md").read_text(encoding="utf-8")
