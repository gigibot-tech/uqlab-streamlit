"""Tests for checkpoint arsenal grouping and config_diff helpers."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from uqlab.evaluation.pipeline.checkpoint_arsenal import (
    build_checkpoint_arsenal,
    filter_arsenal_sections,
)
from uqlab.evaluation.pipeline.config_diff import (
    arsenal_tracked_flat,
    chip_display_label,
    chip_tooltip_lines,
    common_tracked_params,
    diffs_from_common,
    disambiguate_suffix_ids,
)


def _write_checkpoint_run(
    experiments_dir: Path,
    run_id: str,
    *,
    arch: str = "resnet18_mcdropout",
    under_train: int = 300,
    noise: float = 0,
    created_at: datetime | None = None,
) -> dict:
    base = experiments_dir / run_id
    results = base / "results"
    results.mkdir(parents=True)
    (results / "checkpoint.pt").write_bytes(b"stub")
    cfg = {
        "seed": 42,
        "data": {
            "dataset_name": "cifar10",
            "under_train_per_class": under_train,
            "regular_train_per_class": 300,
            "aleatoric_noise_percentage": noise,
        },
        "model": {"architecture": arch, "hidden_dim": 256, "dropout": 0.0},
        "training": {
            "epochs": 12,
            "learning_rate": 0.001,
            "weight_decay": 0.0001,
            "train_batch_size": 256,
        },
        "evaluation": {"mc_passes": 10},
    }
    with (base / "config.yaml").open("w", encoding="utf-8") as handle:
        yaml.dump(cfg, handle)
    return {
        "id": run_id,
        "name": f"run_{run_id[:8]}",
        "status": "completed",
        "created_at": created_at or datetime(2025, 6, 20, 14, 30),
    }


def test_disambiguate_suffix_ids_extends_on_collision() -> None:
    ids = [
        "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa1",
        "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbb1",
    ]
    labels = disambiguate_suffix_ids(ids, start=4, max_len=12)
    assert labels[ids[0]] != labels[ids[1]]
    assert len(labels[ids[0]]) >= 4


def test_common_tracked_params_mode_and_diffs() -> None:
    configs = [
        {
            "data": {"dataset_name": "cifar10", "under_train_per_class": 300},
            "model": {"architecture": "resnet18_mcdropout", "hidden_dim": 256},
            "training": {"epochs": 12, "learning_rate": 0.001},
        },
        {
            "data": {"dataset_name": "cifar10", "under_train_per_class": 200},
            "model": {"architecture": "resnet18_mcdropout", "hidden_dim": 256},
            "training": {"epochs": 12, "learning_rate": 0.001},
        },
    ]
    common = common_tracked_params(configs)
    assert common.get("Epochs") == "12"
    diffs = diffs_from_common(configs, configs[1])
    keys = {d.key for d in diffs}
    assert "data.under_train_per_class" in keys


def test_build_checkpoint_arsenal_clusters_by_shared_config(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "data" / "experiments"
    experiments_dir.mkdir(parents=True)
    id_a = "11111111-1111-1111-1111-111111111111"
    id_b = "22222222-2222-2222-2222-222222222222"
    id_c = "33333333-3333-3333-3333-333333333333"
    exps = [
        _write_checkpoint_run(
            experiments_dir,
            id_a,
            under_train=300,
            noise=0,
            created_at=datetime(2025, 6, 20, 10, 0),
        ),
        _write_checkpoint_run(
            experiments_dir,
            id_b,
            under_train=300,
            noise=50,
            created_at=datetime(2025, 6, 21, 11, 0),
        ),
        _write_checkpoint_run(
            experiments_dir,
            id_c,
            under_train=200,
            noise=0,
            created_at=datetime(2025, 6, 22, 12, 0),
        ),
    ]
    arsenal = build_checkpoint_arsenal(exps, experiments_dir)
    assert arsenal.n_checkpoints == 3
    section = arsenal.sections[0]
    assert section.model_label == "ResNet18"
    assert section.shared_baseline.get("Dataset") == "cifar10"
    assert len(section.config_clusters) == 1
    cluster = section.config_clusters[0]
    assert cluster.n_checkpoints == 3
    assert "Label noise (%)" in cluster.varying_labels
    assert "Under-train / class" in cluster.varying_labels
    assert cluster.row_header().startswith("Varies:")
    labels = {c.display_label for c in cluster.chips}
    assert "50%·u300" in labels
    assert "0%·u300" in labels
    assert "0%·u200" in labels
    chip_50 = next(c for c in cluster.chips if c.display_label == "50%·u300")
    tip = chip_50.tooltip_lines
    assert any("50" in line for line in tip)
    assert not any("→" in line for line in tip)


def test_under_train_varying_clusters_as_chips(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "data" / "experiments"
    experiments_dir.mkdir(parents=True)
    id_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    id_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    exps = [
        _write_checkpoint_run(experiments_dir, id_a, under_train=100, noise=0),
        _write_checkpoint_run(experiments_dir, id_b, under_train=200, noise=0),
    ]
    arsenal = build_checkpoint_arsenal(exps, experiments_dir)
    assert len(arsenal.sections[0].config_clusters) == 1
    cluster = arsenal.sections[0].config_clusters[0]
    labels = {c.display_label for c in cluster.chips}
    assert "u100" in labels
    assert "u200" in labels


def test_chip_display_label_noise_and_under() -> None:
    flat_noise = arsenal_tracked_flat(
        {"data": {"aleatoric_noise_percentage": 50, "under_train_per_class": 300}}
    )
    assert chip_display_label(flat_noise, ("data.aleatoric_noise_percentage",)) == "50%"
    flat_under = arsenal_tracked_flat({"data": {"under_train_per_class": 200}})
    assert chip_display_label(flat_under, ("data.under_train_per_class",)) == "u200"
    assert (
        chip_display_label(
            flat_noise,
            ("data.aleatoric_noise_percentage", "data.under_train_per_class"),
        )
        == "50%·u300"
    )


def test_filter_arsenal_sections_by_model_and_singletons(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "data" / "experiments"
    experiments_dir.mkdir(parents=True)

    def _run(run_id: str, *, noise: float, epochs: int = 12) -> dict:
        base = experiments_dir / run_id
        results = base / "results"
        results.mkdir(parents=True)
        (results / "checkpoint.pt").write_bytes(b"stub")
        cfg = {
            "data": {
                "dataset_name": "cifar10",
                "under_train_per_class": 300,
                "regular_train_per_class": 300,
                "aleatoric_noise_percentage": noise,
            },
            "model": {"architecture": "resnet18_mcdropout", "hidden_dim": 256, "dropout": 0.0},
            "training": {
                "epochs": epochs,
                "learning_rate": 0.001,
                "weight_decay": 0.0001,
                "train_batch_size": 256,
            },
            "evaluation": {"mc_passes": 10},
        }
        with (base / "config.yaml").open("w", encoding="utf-8") as handle:
            yaml.dump(cfg, handle)
        return {
            "id": run_id,
            "name": f"run_{run_id[:8]}",
            "status": "completed",
            "created_at": datetime(2025, 6, 20, 14, 30),
        }

    exps = [
        _run("11111111-1111-1111-1111-111111111111", noise=0),
        _run("22222222-2222-2222-2222-222222222222", noise=50),
        _run("33333333-3333-3333-3333-333333333333", noise=0, epochs=24),
    ]
    arsenal = build_checkpoint_arsenal(exps, experiments_dir)
    filtered = filter_arsenal_sections(arsenal, sweep_axis="Label noise (%)")
    assert filtered.n_checkpoints == 2
    hidden = filter_arsenal_sections(arsenal, hide_singletons=True)
    assert hidden.n_checkpoints == 2
    assert all(c.n_checkpoints > 1 for s in hidden.sections for c in s.config_clusters)


def test_chip_tooltip_from_run_name() -> None:
    flat = arsenal_tracked_flat(
        {
            "data": {"dataset_name": "cifar10", "aleatoric_noise_percentage": 50},
            "model": {"architecture": "resnet18_mcdropout"},
            "training": {"epochs": 12},
        }
    )
    lines = chip_tooltip_lines(
        name="fast_alea_20260616_143426_noise_50",
        flat=flat,
        cluster_flats=[flat],
        experiment_id="deb5d36f-5a27-4fe2-9a3c-02ece38a0b92",
    )
    assert any("Label noise (%): 50" in line for line in lines)
    assert not any("signals" in line.lower() for line in lines)
    assert not any("→" in line for line in lines)


def test_build_checkpoint_arsenal_empty_without_checkpoint_pt(tmp_path: Path) -> None:
    experiments_dir = tmp_path / "data" / "experiments"
    run_id = "44444444-4444-4444-4444-444444444444"
    base = experiments_dir / run_id
    base.mkdir(parents=True)
    with (base / "config.yaml").open("w", encoding="utf-8") as handle:
        yaml.dump({"model": {"architecture": "resnet18_mcdropout"}}, handle)
    exps = [{"id": run_id, "status": "completed", "created_at": datetime(2025, 6, 20)}]
    arsenal = build_checkpoint_arsenal(exps, experiments_dir)
    assert arsenal.is_empty
