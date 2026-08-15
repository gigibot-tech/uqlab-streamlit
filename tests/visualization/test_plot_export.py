"""Tests for plot PNG export helpers."""

from __future__ import annotations

from uqlab.ui_components.visualization.plot_export import (
    matplotlib_png_from_line_payload,
    plotly_figure_to_png_bytes,
    sweep_plot_filename,
)
from uqlab.ui_components.visualization.sweeps.sweep_line_plot_viz import figure_from_payload


def _sample_payload() -> dict:
    return {
        "sweep_kind": "label_noise",
        "x_label": "Label noise (%)",
        "signal": "entropy",
        "y_left_title": "Entropy mean (aleatoric)",
        "y_right_title": "Accuracy",
        "traces": [
            {
                "name": "entropy_mean_aleatoric",
                "x": [0, 20, 40],
                "y": [0.1, 0.2, 0.3],
                "color": "#1f77b4",
            },
            {
                "name": "accuracy",
                "x": [0, 20, 40],
                "y": [0.9, 0.85, 0.8],
                "color": "#2ca02c",
                "yaxis": "right",
            },
        ],
    }


def test_sweep_plot_filename_is_png():
    name = sweep_plot_filename(_sample_payload(), prefix="sweep_line_plot")
    assert name.endswith(".png")
    assert "label_noise" in name
    assert "entropy" in name


def test_matplotlib_png_from_line_payload_returns_bytes():
    png = matplotlib_png_from_line_payload(_sample_payload())
    assert isinstance(png, bytes)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_plotly_figure_to_png_bytes_when_kaleido_available():
    fig = figure_from_payload(_sample_payload())
    png, err = plotly_figure_to_png_bytes(fig)
    if png is None:
        assert err
    else:
        assert png[:8] == b"\x89PNG\r\n\x1a\n"
