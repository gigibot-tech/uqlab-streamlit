"""Tests for campaign section splitting."""

from __future__ import annotations

from pathlib import Path

import torch
import yaml

from uqlab.evaluation.reporting.campaign_sections import split_campaign_sections


def _minimal_run(exp_dir: Path, run_id: str, name: str, cfg: dict) -> None:
    base = exp_dir / run_id / "results"
    base.mkdir(parents=True)
    (exp_dir / run_id / "config.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    n = 20
    torch.save(
        {
            "signal_table": {"inverse_coherence": torch.linspace(0.1, 0.5, n)},
            "eval_group_labels": torch.cat([torch.zeros(10), torch.ones(10)]),
            "predictions": torch.zeros(n),
            "eval_clean_labels": torch.zeros(n),
        },
        base / "results.pt",
    )
    (base / "summary.json").write_text("{}", encoding="utf-8")


def test_single_section_fallback(tmp_path):
    exp_dir = tmp_path / "experiments"
    for i, noise in enumerate((0, 25)):
        rid = f"legacy-{i}"
        _minimal_run(
            exp_dir,
            rid,
            f"run_{noise}",
            {"data": {"aleatoric_noise_percentage": noise, "under_train_per_class": 300}},
        )
    exps = [
        {"id": "legacy-0", "status": "completed", "name": "run_0"},
        {"id": "legacy-1", "status": "completed", "name": "run_25"},
    ]
    sections = split_campaign_sections(exps, experiments_dir=exp_dir)
    assert len(sections) == 1
    assert sections[0].label == "Campaign sweep"
