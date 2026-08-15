"""Tests for four-region reporting helpers."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from uqlab.evaluation.reporting.four_region_reporting import (
    four_region_signals_dataframe,
    list_four_region_signal_columns,
    plot_four_region_metrics_by_group,
)


def test_four_region_signals_dataframe(tmp_path: Path) -> None:
    csv = tmp_path / "per_sample_signals.csv"
    csv.write_text(
        "group,dataset_index,inverse_coherence_dualxda,expected_entropy\n"
        "clean,0,0.1,0.2\n"
        "aleatoric_like,1,0.5,0.6\n"
        "epistemic_like,2,0.3,0.4\n"
        "ood_like,3,0.9,0.8\n"
    )
    df = four_region_signals_dataframe(tmp_path)
    assert len(df) == 4
    assert set(df["group"]) == {"clean", "aleatoric_like", "epistemic_like", "ood_like"}


def test_list_four_region_signal_columns() -> None:
    df = pd.DataFrame(
        {
            "group": ["clean"],
            "dataset_index": [0],
            "inverse_coherence_dualxda": [0.1],
            "is_noisy": [False],
        }
    )
    cols = list_four_region_signal_columns(df)
    assert cols == ["inverse_coherence_dualxda"]


def test_plot_four_region_metrics_by_group(tmp_path: Path) -> None:
    df = pd.DataFrame(
        {
            "group": ["clean", "clean", "ood_like"],
            "inverse_coherence_dualxda": [0.1, 0.2, 0.9],
        }
    )
    out_dir = tmp_path / "plots"
    paths = plot_four_region_metrics_by_group(
        df,
        ["inverse_coherence_dualxda"],
        out_dir,
        title_prefix="test",
    )
    assert len(paths) == 1
    assert paths[0].is_file()


def test_four_region_signals_dataframe_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        four_region_signals_dataframe(tmp_path)
