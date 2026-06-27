#!/usr/bin/env python3
"""Post-hoc disentanglement scoring and paper-style curve plots from finished runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from uqlab.evaluation.benchmarks.disentangling.bridge_sweep import (  # noqa: E402
    score_bridge_pair_with_vendor_metric,
    score_bridge_pairs_from_results,
)
from uqlab.evaluation.reporting.paper_benchmark_plot import (  # noqa: E402
    PAPER_TRACE_COLORS,
    PAPER_TRACE_LABELS,
    build_paper_benchmark_plot,
    save_paper_benchmark_png,
)
from uqlab.evaluation.reporting.sweep_line_plot import (  # noqa: E402
    SWEEP_KIND_DATASET_SIZE,
    SWEEP_KIND_LABEL_NOISE,
)
from uqlab.runtime_paths import experiments_root  # noqa: E402


def _resolve_results_pt(results_dir: Path) -> Path:
    results_dir = results_dir.resolve()
    direct = results_dir / "results.pt"
    if direct.is_file():
        return direct
    nested = results_dir / "results" / "results.pt"
    if nested.is_file():
        return nested
    raise FileNotFoundError(
        f"No results.pt under {results_dir} (tried results.pt and results/results.pt)"
    )


def _parse_run_ids(raw: str | None, campaign_dir: Path | None) -> list[str]:
    if raw:
        return [part.strip() for part in raw.split(",") if part.strip()]
    if campaign_dir is None:
        raise ValueError("Provide --run-ids or --campaign-dir")
    campaign_dir = campaign_dir.resolve()
    if not campaign_dir.is_dir():
        raise FileNotFoundError(f"Campaign dir not found: {campaign_dir}")
    return sorted(p.name for p in campaign_dir.iterdir() if p.is_dir())


def cmd_score(args: argparse.Namespace) -> int:
    results_path = _resolve_results_pt(args.results_dir)
    if args.all_presets:
        rows = score_bridge_pairs_from_results(results_path, modes=args.modes)
        df = pd.DataFrame(rows)
        out = args.output or (args.results_dir / "disentanglement_scores.csv")
        df.to_csv(out, index=False)
        print(f"Wrote {len(df)} preset row(s) -> {out}")
        return 0

    score = score_bridge_pair_with_vendor_metric(
        results_path,
        predict_mode=args.mode,
        aleatoric_signal=args.aleatoric_signal,
        epistemic_signal=args.epistemic_signal,
    )
    row = {
        "results_path": str(results_path),
        "mode": args.mode,
        "aleatoric_signal": args.aleatoric_signal,
        "epistemic_signal": args.epistemic_signal,
        "disentanglement_score": score,
    }
    out = args.output or (args.results_dir / "disentanglement_score.csv")
    pd.DataFrame([row]).to_csv(out, index=False)
    print(f"disentanglement score: {score:.6f}")
    print(f"Wrote {out}")
    return 0


def _render_matplotlib(payload, out_dir: Path, *, per_metric: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    combined = out_dir / f"{payload.sweep_kind}_three_line.png"
    save_paper_benchmark_png(payload, combined)
    print(f"Wrote {combined}")

    if not per_metric:
        return

    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise SystemExit("matplotlib required for --per-metric-plots") from exc

    x_vals = payload.traces[0]["x"] if payload.traces else []
    for trace in payload.traces:
        metric = trace["metric"]
        fig_m, ax_m = plt.subplots(figsize=(7, 4))
        ax_m.plot(
            x_vals,
            trace["y"],
            marker="o",
            color=trace.get("color") or PAPER_TRACE_COLORS.get(metric, "#333"),
            label=PAPER_TRACE_LABELS.get(metric, metric),
        )
        ax_m.set_xlabel(payload.x_label)
        ax_m.set_ylabel(trace["name"])
        ax_m.set_ylim(0, 1)
        ax_m.set_title(f"{payload.experiment} — {metric}")
        fig_m.tight_layout()
        metric_path = out_dir / f"{payload.sweep_kind}_{metric}.png"
        fig_m.savefig(metric_path, dpi=150)
        plt.close(fig_m)
        print(f"Wrote {metric_path}")


def cmd_curves(args: argparse.Namespace) -> int:
    exp_dir = (args.experiments_dir or experiments_root()).resolve()
    run_ids = _parse_run_ids(args.run_ids, args.campaign_dir)
    if not run_ids:
        raise SystemExit("No run IDs found")

    payload = build_paper_benchmark_plot(
        run_ids,
        exp_dir,
        sweep_kind=args.sweep_kind,
        aleatoric_signal=args.aleatoric_signal,
        epistemic_signal=args.epistemic_signal,
        rank_correlation=args.rank_correlation,
    )

    out_dir = (args.out_dir or Path.cwd() / "disentanglement_curves").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    wide_rows: list[dict] = []
    x_vals = payload.traces[0]["x"] if payload.traces else []
    metric_by_name = {t["metric"]: t["y"] for t in payload.traces}
    for idx, pct in enumerate(x_vals):
        wide_rows.append(
            {
                "Experiment": payload.experiment,
                "Percentage": pct,
                "scores": metric_by_name.get("scores", [None] * len(x_vals))[idx],
                "aleatorics": metric_by_name.get("aleatorics", [None] * len(x_vals))[idx],
                "epistemics": metric_by_name.get("epistemics", [None] * len(x_vals))[idx],
                "run_id": payload.run_ids[idx] if idx < len(payload.run_ids) else None,
            }
        )
    curves_csv = out_dir / f"{args.sweep_kind}_curves.csv"
    pd.DataFrame(wide_rows).to_csv(curves_csv, index=False)
    print(f"Wrote {curves_csv} ({len(wide_rows)} points)")

    long_csv = out_dir / f"{args.sweep_kind}_curves_long.csv"
    long_rows: list[dict] = []
    for row in wide_rows:
        for metric in ("scores", "aleatorics", "epistemics"):
            val = row.get(metric)
            if val is None:
                continue
            long_rows.append(
                {
                    "Experiment": row["Experiment"],
                    "Percentage": row["Percentage"],
                    "metric": metric,
                    "value": val,
                    "Run_Index": 0,
                    "run_id": row.get("run_id"),
                }
            )
    pd.DataFrame(long_rows).to_csv(long_csv, index=False)
    print(f"Wrote {long_csv}")

    if args.plot:
        _render_matplotlib(payload, out_dir, per_metric=args.per_metric_plots)

    corr = payload.correlations
    if corr:
        print(f"Correlations: {corr}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Post-hoc disentanglement score and paper curves from results.pt runs"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    score_p = sub.add_parser("score", help="Score one finished run")
    score_p.add_argument(
        "--results-dir",
        type=Path,
        required=True,
        help="Run output dir containing results.pt (or results/results.pt)",
    )
    score_p.add_argument(
        "--mode",
        default="paper",
        choices=["paper", "signal", "signal_dualxda", "signal_ek_fak"],
        help="Bridge preset when not using --all-presets",
    )
    score_p.add_argument("--aleatoric-signal", default=None)
    score_p.add_argument("--epistemic-signal", default=None)
    score_p.add_argument(
        "--all-presets",
        action="store_true",
        help="Score all bridge presets (no vendor scalar; summary table)",
    )
    score_p.add_argument(
        "--modes",
        nargs="*",
        default=None,
        help="Limit presets when using --all-presets",
    )
    score_p.add_argument("--output", type=Path, default=None)
    score_p.set_defaults(func=cmd_score)

    curves_p = sub.add_parser("curves", help="Build paper curves from a sweep campaign")
    curves_p.add_argument(
        "--experiments-dir",
        type=Path,
        default=None,
        help=f"Root with run folders (default: {experiments_root()})",
    )
    curves_p.add_argument(
        "--campaign-dir",
        type=Path,
        default=None,
        help="Directory whose child folders are run IDs (alternative to --run-ids)",
    )
    curves_p.add_argument(
        "--run-ids",
        type=str,
        default=None,
        help="Comma-separated run IDs under experiments-dir",
    )
    curves_p.add_argument(
        "--sweep-kind",
        required=True,
        choices=[SWEEP_KIND_LABEL_NOISE, SWEEP_KIND_DATASET_SIZE],
    )
    curves_p.add_argument("--aleatoric-signal", default=None)
    curves_p.add_argument("--epistemic-signal", default=None)
    curves_p.add_argument("--rank-correlation", action="store_true")
    curves_p.add_argument("--out-dir", type=Path, default=None)
    curves_p.add_argument(
        "--plot",
        action="store_true",
        help="Write matplotlib PNG(s) for the three-line paper plot",
    )
    curves_p.add_argument(
        "--per-metric-plots",
        action="store_true",
        help="Also write one PNG per metric (scores, aleatorics, epistemics)",
    )
    curves_p.set_defaults(func=cmd_curves)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
