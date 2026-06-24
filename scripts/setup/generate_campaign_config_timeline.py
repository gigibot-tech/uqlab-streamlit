#!/usr/bin/env python3
"""
Export a compact config timeline figure for a sweep campaign.

Shows shared baseline config once, then per-run steps with Δparams vs the previous run.

Example
-------
  cd uqlab-streamlit
  PYTHONPATH=src python3 scripts/generate_campaign_config_timeline.py \\
    --run-ids uuid1,uuid2,uuid3 \\
    -o /tmp/campaign_timeline.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _parse_facets(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            continue
        key, val = item.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build campaign config timeline PDF/PNG.")
    parser.add_argument(
        "--run-ids",
        required=True,
        help="Comma-separated experiment UUIDs (completed runs with config.yaml).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=PROJECT_ROOT / "campaign_timeline.pdf",
        help="Output path (.pdf or .png).",
    )
    parser.add_argument(
        "--experiments-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "experiments",
        help="On-disk experiments root.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
    )
    parser.add_argument(
        "--sweep-kind",
        choices=("auto", "label_noise", "dataset_size"),
        default="auto",
    )
    parser.add_argument(
        "--facet",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Facet filter, e.g. learning_rate=0.001 (repeatable).",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Report title override.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=150,
    )
    args = parser.parse_args(argv)

    from uqlab.evaluation.pipeline.campaign_config_timeline import (
        build_campaign_timeline,
        build_campaign_timeline_figure,
        save_timeline_figure,
    )

    run_ids = [r.strip() for r in args.run_ids.split(",") if r.strip()]
    experiments = [{"id": rid, "status": "completed", "name": rid[:8]} for rid in run_ids]
    sweep_kind = None if args.sweep_kind == "auto" else args.sweep_kind
    facet_filters = _parse_facets(args.facet) or None

    try:
        timeline = build_campaign_timeline(
            experiments,
            args.experiments_dir.resolve(),
            project_root=args.project_root.resolve(),
            sweep_kind=sweep_kind,
            facet_filters=facet_filters,
            title=args.title,
            apply_facet_filters=bool(facet_filters),
        )
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        return 1

    fig = build_campaign_timeline_figure(timeline)
    saved = save_timeline_figure(fig, args.output.resolve(), dpi=args.dpi)
    print(f"Campaign: {timeline.title}")
    print(f"Sweeps: {timeline.n_runs}")
    print(f"Wrote {saved}")

    import matplotlib.pyplot as plt

    plt.close(fig)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
