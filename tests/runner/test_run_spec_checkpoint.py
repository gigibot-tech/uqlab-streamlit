"""Tests for checkpoint resume YAML epoch semantics."""

from __future__ import annotations

from pathlib import Path

from uqlab_orchestrator.config import merge_workflow_defaults
from uqlab_orchestrator.run_spec import build_run_yaml


def test_resume_writes_additional_epochs_not_total():
    workflow = merge_workflow_defaults({})
    workflow["training_config"].update(
        {
            "use_checkpoint": True,
            "checkpoint_id": "abc123",
            "prior_epochs": 12,
            "additional_epochs": 10,
            "epochs": 22,
        }
    )
    cfg = build_run_yaml(workflow)
    assert cfg["training"]["epochs"] == 10
    assert cfg["training"].get("prior_epochs") == 12


def test_resume_sweep_checkpoint_map_per_point(tmp_path, monkeypatch):
    exp_id = "deadbeef-dead-beef-dead-beefdeadbeef"
    ckpt_dir = tmp_path / "data" / "experiments" / exp_id / "results"
    ckpt_dir.mkdir(parents=True)
    (ckpt_dir / "checkpoint.pt").write_bytes(b"fake")

    import uqlab_orchestrator.run_spec as run_spec

    monkeypatch.setattr(
        run_spec,
        "_checkpoint_path_for_experiment",
        lambda eid: str(ckpt_dir / "checkpoint.pt") if eid == exp_id else None,
    )

    workflow = merge_workflow_defaults({})
    workflow["training_config"].update(
        {
            "use_checkpoint": True,
            "checkpoint_id": exp_id,
            "prior_epochs": 2,
            "additional_epochs": 8,
            "epochs": 10,
        }
    )
    workflow["resume_checkpoints"] = {"noise:25": exp_id}

    cfg = build_run_yaml(workflow, aleatoric_noise_percentage=25.0)
    assert cfg["model"].get("checkpoint_path")
    assert Path(cfg["model"]["checkpoint_path"]).exists()
    assert cfg["training"]["epochs"] == 8
