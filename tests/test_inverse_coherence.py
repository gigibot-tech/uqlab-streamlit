"""Top-k coherence must vary; global-style cancellation should not saturate at 1."""

import sys
from pathlib import Path

import torch

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "src"))
sys.path.insert(0, str(_root))

from uqlab.evaluation.signals.attribution import (  # noqa: E402
    build_fast_pilot_signal_table,
    inverse_coherence_from_coherence,
    map_attribution_structure_to_uncertainty,
    reciprocal_uncertainty,
    topk_influence_metrics,
)


def test_coherence_high_when_supporters_align():
    row = torch.zeros(100)
    row[0] = 5.0
    row[1] = 0.1
    coh, mass, dom = topk_influence_metrics(row, top_k=2)
    assert mass > 0
    assert coh > 0.9
    assert dom > 0.9
    assert coh > 0.9
    inv = inverse_coherence_from_coherence(torch.tensor([coh])).item()
    assert inv < 0.2


def test_coherence_low_when_supporters_cancel():
    row = torch.zeros(100)
    row[0] = 1.0
    row[1] = 1.0
    row[2] = -0.95
    row[3] = -0.95
    coh, mass, dom = topk_influence_metrics(row, top_k=4)
    assert mass > 0
    assert coh < 0.2
    inv = inverse_coherence_from_coherence(torch.tensor([coh])).item()
    assert inv > 0.7


def test_topk_mass_enables_inverse_mass():
    row = torch.zeros(50)
    row[:3] = torch.tensor([2.0, 1.5, 1.0])
    _, mass, _ = topk_influence_metrics(row, top_k=3)
    inv = reciprocal_uncertainty(torch.tensor([mass])).item()
    assert inv > 0.01


def test_map_and_build_fast_pilot_share_inverse_coherence():
    n = 8
    raw = {
        "coherence": torch.linspace(0.2, 0.9, n),
        "mass": torch.ones(n) * 0.5,
        "dominance": torch.ones(n) * 0.1,
        "label_disagreement": torch.zeros(n),
        "noisy_support_ratio": torch.zeros(n),
        "attribution_concentration": torch.zeros(n),
        "cross_class_support": torch.zeros(n),
    }
    raw["inverse_coherence"] = inverse_coherence_from_coherence(raw["coherence"])
    mapped = map_attribution_structure_to_uncertainty(raw)
    table = build_fast_pilot_signal_table(
        attribution_signals=raw,
        det_logits=torch.randn(n, 10),
        mean_pred_det=torch.softmax(torch.randn(n, 10), dim=1),
        mc_uq={
            "mean_prediction": torch.softmax(torch.randn(n, 10), dim=1),
            "entropy": torch.ones(n),
            "mutual_info": torch.ones(n) * 0.1,
        },
        enabled={"inverse_coherence"},
    )
    assert torch.allclose(mapped["inverse_coherence"], table["inverse_coherence"])


if __name__ == "__main__":
    test_coherence_high_when_supporters_align()
    test_coherence_low_when_supporters_cancel()
    test_map_and_build_fast_pilot_share_inverse_coherence()
    print("ok")
