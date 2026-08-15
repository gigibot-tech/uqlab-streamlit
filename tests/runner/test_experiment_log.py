"""Tests for per-experiment log capture."""

from __future__ import annotations

from pathlib import Path

from uqlab.runner.experiment_log import (
    EXPERIMENT_LOG_FILENAME,
    capture_experiment_log,
    experiment_log_path,
    infer_experiment_id,
)


def test_capture_experiment_log_tees_stdout(tmp_path: Path) -> None:
    results_dir = tmp_path / "exp-uuid" / "results"
    results_dir.mkdir(parents=True)
    config_path = tmp_path / "exp-uuid" / "config.yaml"
    config_path.write_text("seed: 1\n", encoding="utf-8")

    with capture_experiment_log(results_dir, config_path=config_path):
        print("hello from experiment")
        print("second line", flush=True)

    log_path = experiment_log_path(results_dir)
    assert log_path.is_file()
    text = log_path.read_text(encoding="utf-8")
    assert "Experiment ID: exp-uuid" in text
    assert "hello from experiment" in text
    assert "second line" in text
    assert "EXPERIMENT LOG — completed" in text


def test_capture_experiment_log_records_failure(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir(parents=True)

    try:
        with capture_experiment_log(results_dir):
            raise RuntimeError("boom")
    except RuntimeError:
        pass

    text = experiment_log_path(results_dir).read_text(encoding="utf-8")
    assert "RuntimeError: boom" in text
    assert "EXPERIMENT LOG — failed" in text


def test_infer_experiment_id_from_results_dir(tmp_path: Path) -> None:
    exp_dir = tmp_path / "abc-123"
    (exp_dir / "results").mkdir(parents=True)
    (exp_dir / "config.yaml").write_text("x: 1\n", encoding="utf-8")
    assert infer_experiment_id(results_dir=exp_dir / "results") == "abc-123"


def test_experiment_log_filename_constant() -> None:
    assert EXPERIMENT_LOG_FILENAME == "experiment.log"
