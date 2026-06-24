#!/usr/bin/env python3
"""
Run four-region validation sweep analysis (Aspect 7).

With ``--mock``, uses synthetic metric rows to demonstrate the correlation report.
With ``--metrics-json``, loads pre-aggregated sweep rows from a JSON file::

    {
      "noise_rows": [{"noise_pct": 0, "inverse_coherence_graddot": 0.1, ...}, ...],
      "sparsity_rows": [{"sparse_train_pct": 1, "inverse_mass_graddot": 0.9, ...}, ...]
    }

Sweep region presets (for launching real jobs) are printed with ``--list-sweeps``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uqlab.evaluation.four_region_validation import (  # noqa: E402
    NOISE_SWEEP_PCTS,
    SPARSITY_SWEEP_PCTS,
    build_correlation_report,
    mock_sweep_metric_rows,
    noise_sweep_regions,
    report_to_json,
    sparsity_sweep_regions,
)


def _print_sweep_presets() -> None:
    print("Noise sweep (noisy region label_flip_pct):")
    for pct, _ in noise_sweep_regions():
        print(f"  - {pct}%")
    print("\nSparsity sweep (sparse region train_fraction):")
    for pct, regions in sparsity_sweep_regions():
        frac = regions["sparse"]["train_fraction"]
        print(f"  - {pct}% ({frac})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Four-region validation correlation report")
    parser.add_argument("--mock", action="store_true", help="Use synthetic ideal sweep rows")
    parser.add_argument(
        "--metrics-json",
        type=Path,
        help="JSON file with noise_rows and sparsity_rows metric aggregates",
    )
    parser.add_argument("--output", type=Path, help="Write JSON report to this path")
    parser.add_argument(
        "--list-sweeps",
        action="store_true",
        help=f"Print sweep axes ({len(NOISE_SWEEP_PCTS)} noise, {len(SPARSITY_SWEEP_PCTS)} sparsity)",
    )
    args = parser.parse_args()

    if args.list_sweeps:
        _print_sweep_presets()
        return 0

    if args.mock:
        noise_rows, sparsity_rows = mock_sweep_metric_rows()
    elif args.metrics_json:
        payload = json.loads(args.metrics_json.read_text())
        noise_rows = payload["noise_rows"]
        sparsity_rows = payload["sparsity_rows"]
    else:
        parser.error("Provide --mock, --metrics-json, or --list-sweeps")
        return 2

    report = build_correlation_report(noise_rows, sparsity_rows)
    text = report_to_json(report)
    print(text)
    if args.output:
        args.output.write_text(text)
        print(f"\nWrote {args.output}", file=sys.stderr)

    return 0 if report.monotonic_passed and report.orthogonal_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
