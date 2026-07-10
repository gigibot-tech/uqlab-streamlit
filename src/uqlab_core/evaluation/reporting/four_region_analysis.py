"""One-call post-hoc analysis for the four-region benchmark notebook."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd
import torch

from uqlab_core.evaluation.reporting.attribution_distribution_summary import (
    DIST_SIGNAL_COLS,
    FOUR_REGION_GROUP_ORDER,
    all_distribution_signal_cols,
    distribution_takeaway_lines,
    four_region_pairwise_auroc_report,
    four_region_signal_group_confusion_report,
    group_mean_table,
    pairwise_takeaway_line,
    summarize_attribution_distribution,
)
from uqlab_core.evaluation.reporting.attribution_rebuild import rebuild_tracer_and_attr
from uqlab_core.evaluation.reporting.eval_pack_diagnostics import (
    load_eval_sizes,
    model_eval_pack_report,
)
from uqlab_core.evaluation.reporting.four_region_reporting import (
    four_region_signals_dataframe,
    list_four_region_signal_columns,
    plot_four_region_metrics_by_group,
    run_four_region_class_diagnostics,
)
from uqlab_core.evaluation.reporting.four_region_synthesis_profile import (
    ReportProfile,
    SYNTHESIS_TASK2_SLICE,
    SYNTHESIS_TASK2_TARGETS,
    is_synthesis_profile,
    print_hi_pr_agreement,
    print_synthesis_step6_summary,
    synthesis_contrast_cols,
    synthesis_plot_metrics,
)
from uqlab_core.evaluation.reporting.signal_spearman_diagnostics import (
    four_region_signal_spearman_report,
)
from uqlab_core.evaluation.reporting.zwischen_audit import (
    audit_zwischen_attribution,
    backfill_distribution_signals_from_zwischen,
    print_zwischen_attribution_audit,
)


def _distribution_backends(*, enable_graddot: bool, enable_ek_fac: bool) -> list[str]:
    backends = ["dualxda"]
    if enable_graddot:
        backends.append("graddot")
    if enable_ek_fac:
        backends.append("ek_fak")
    return backends


def _plot_metrics(
    *,
    enable_graddot: bool,
    enable_ek_fac: bool,
    report_profile: ReportProfile,
) -> list[str]:
    if is_synthesis_profile(report_profile):
        return synthesis_plot_metrics(
            enable_graddot=enable_graddot,
            enable_ek_fac=enable_ek_fac,
        )
    from uqlab_core.evaluation.signals.catalog import (
        AttributionBackend,
        predictive_baseline_ids,
    )

    metrics = [
        "attribution_entropy_dualxda",
        "attribution_participation_dualxda",
        f"coherence_{AttributionBackend.DUALXDA.value}",
        f"inverse_coherence_{AttributionBackend.DUALXDA.value}",
    ]
    if enable_ek_fac:
        metrics.append(f"coherence_{AttributionBackend.EK_FAK.value}")
        metrics.append(f"inverse_coherence_{AttributionBackend.EK_FAK.value}")
    if enable_graddot:
        metrics.append(f"coherence_{AttributionBackend.GRADDOT.value}")
        metrics.append(f"inverse_coherence_{AttributionBackend.GRADDOT.value}")
    metrics.extend(predictive_baseline_ids())
    return metrics


@dataclass
class FourRegionAnalysis:
    """Outputs from :func:`analyze_four_region_run`."""

    df: pd.DataFrame
    plot_paths: list[Path]
    group_stats: pd.DataFrame
    auroc_ranking: pd.DataFrame
    mean_diff: pd.DataFrame
    pair_auroc: pd.DataFrame
    takeaway_lines: list[str]
    pairwise_takeaway: str | None
    signal_group_confusion: pd.DataFrame
    model_pack_report: dict[str, Any]
    class_diagnostics: dict[str, object] | None
    spearman_report: dict[str, Any] | None = None
    hi_pr_rho: float | None = None


def analyze_four_region_run(
    run_dir: Path,
    *,
    title_prefix: str = "",
    device: torch.device | str | None = None,
    enable_graddot: bool = False,
    enable_ek_fac: bool = False,
    max_eval_samples_for_rebuild: int = 200,
    report_profile: ReportProfile = "synthesis",
    log: bool = True,
) -> FourRegionAnalysis:
    """
    Step 6 in one call: box plots, distribution tables, pairwise contrasts.

    ``report_profile="synthesis"`` (default) logs only metrics referenced in
    ``docs/features/four-region-step6-synthesis.tex``. ``report_profile="full"``
    keeps exploratory diagnostics (all pairwise axes, all Spearman slices).

    Reads ``per_sample_signals.csv`` under ``run_dir``. Audits ``zwischen/`` influence
    artifacts, backfills GradDot/EK-FAC distribution columns from saved matrices when
    missing, and rebuilds DualXDA distribution columns via tracer when those are absent.
    """
    run_dir = Path(run_dir)
    synthesis = is_synthesis_profile(report_profile)
    dist_backends = _distribution_backends(
        enable_graddot=enable_graddot,
        enable_ek_fac=enable_ek_fac,
    )
    audit = audit_zwischen_attribution(run_dir)
    if log and not synthesis:
        print_zwischen_attribution_audit(audit)

    metrics = _plot_metrics(
        enable_graddot=enable_graddot,
        enable_ek_fac=enable_ek_fac,
        report_profile=report_profile,
    )
    df = four_region_signals_dataframe(run_dir)

    backfill_targets = [
        b
        for b in dist_backends
        if b != "dualxda" and audit.get("backends", {}).get(b, {}).get("needs_backfill")
    ]
    if backfill_targets:
        df = backfill_distribution_signals_from_zwischen(
            run_dir,
            backfill_targets,
            df=df,
            log=log and not synthesis,
        )

    metrics = [m for m in metrics if m in df.columns] or list_four_region_signal_columns(df)

    out_dir = run_dir / "analysis" / "four_region_metrics"
    plot_paths = plot_four_region_metrics_by_group(
        df,
        metrics,
        out_dir,
        title_prefix=title_prefix or run_dir.name,
        filename_prefix=run_dir.name,
    )
    if log:
        print(f"Saved {len(plot_paths)} plots under {out_dir}")

    missing_dist = [c for c in DIST_SIGNAL_COLS if c not in df.columns]
    if missing_dist:
        if log:
            print(f"Rebuilding DualXDA distribution signals (missing: {missing_dist})")
        dev = torch.device(device or "cpu")
        rebuilt = rebuild_tracer_and_attr(
            run_dir,
            device=dev,
            max_eval_samples=max_eval_samples_for_rebuild,
        )
        n = int(rebuilt["attr"].shape[0])
        df = df.iloc[:n].copy().reset_index(drop=True)
        for key, col in zip(
            ("entropy", "participation", "signed_split", "variance"),
            DIST_SIGNAL_COLS,
            strict=True,
        ):
            df[col] = rebuilt["distribution"][key].numpy()

    dist_cols = [c for c in all_distribution_signal_cols(dist_backends) if c in df.columns]
    if not dist_cols:
        dist_cols = list(DIST_SIGNAL_COLS)

    region_order = [g for g in FOUR_REGION_GROUP_ORDER if g in df["group"].unique()]
    group_stats, auroc_ranking = summarize_attribution_distribution(
        df,
        dist_cols=dist_cols,
        region_order=region_order,
        baseline_cols=["coherence_dualxda", "inverse_coherence_dualxda"],
    )

    if log and not synthesis:
        print("\nAttribution distribution (full influence vector) — group means")
        print(group_mean_table(group_stats).to_string(float_format=lambda x: f"{x:.4f}"))

        print("\nAUROC (aleatoric_like vs epistemic_like):")
        for _, row in auroc_ranking.iterrows():
            auroc = row["auroc"]
            if pd.isna(auroc):
                reason = row.get("skip_reason", "undefined")
                print(f"  {row['signal']:38s}  —  {reason}")
            else:
                print(f"  {row['signal']:38s}  {float(auroc):.3f}")

    takeaway_lines = distribution_takeaway_lines(
        group_stats.xs("mean", axis=1, level=1),
        auroc_ranking,
    )
    if log and takeaway_lines and not synthesis:
        print("\nTakeaway:")
        for line in takeaway_lines:
            print(f"  {line}")

    contrast_cols = synthesis_contrast_cols(df, extra=metrics) if synthesis else [
        c
        for c in (*dist_cols, "coherence_dualxda", "inverse_coherence_dualxda", *metrics)
        if c in df.columns
    ]
    if not synthesis:
        contrast_cols = list(dict.fromkeys(contrast_cols))

    pairwise_report = four_region_pairwise_auroc_report(
        df,
        contrast_cols,
        out_dir=out_dir,
        log=log and not synthesis,
        log_profile=report_profile,
    )
    mean_diff = pairwise_report["mean_diff"]
    pair_auroc = pairwise_report["pair_auroc"]

    if log and not synthesis:
        print("\nPairwise signal mean differences (left group − right group)")
        print(mean_diff.to_string(float_format=lambda x: f"{x:+.4f}"))

    pair_line = pairwise_takeaway_line(mean_diff, signal_short="signed_split")
    if log and pair_line and not synthesis:
        print(f"\nPairwise takeaway: {pair_line}")

    class_diagnostics: dict[str, object] | None = None
    if not synthesis:
        class_diagnostics = run_four_region_class_diagnostics(
            df,
            contrast_cols,
            out_dir,
            title_prefix=title_prefix or run_dir.name,
            filename_prefix=run_dir.name,
        )
        if log:
            print(
                f"\nClass diagnostics: {len(class_diagnostics['plot_paths'])} plots "
                f"(by_clean_label/ + ecdf/)"
            )
            if class_diagnostics.get("threshold_csv") is not None:
                print(f"  Fraction > 0.5: {class_diagnostics['threshold_csv']}")

    signal_cm_report = four_region_signal_group_confusion_report(
        df,
        contrast_cols,
        out_dir=out_dir,
        log=log and not synthesis,
    )

    model_report = model_eval_pack_report(
        run_dir,
        eval_sizes=load_eval_sizes(run_dir),
        out_dir=out_dir,
        log=log,
        log_profile=report_profile,
    )

    spearman_slices = [SYNTHESIS_TASK2_SLICE] if synthesis else None
    if synthesis:
        spearman_targets = list(SYNTHESIS_TASK2_TARGETS)
    else:
        from uqlab_core.evaluation.reporting.signal_spearman_diagnostics import (
            DEFAULT_TARGETS,
        )

        spearman_targets = list(DEFAULT_TARGETS)

    spearman_report = four_region_signal_spearman_report(
        run_dir,
        df=df,
        signal_cols=contrast_cols,
        targets=spearman_targets,
        slices=spearman_slices,
        out_dir=out_dir,
        log=log and not synthesis,
        log_profile=report_profile,
        stratify_by_clean_label=not synthesis,
    )

    hi_pr_rho = print_hi_pr_agreement(df, log=False)

    if log and synthesis:
        print_synthesis_step6_summary(
            df=df,
            pair_auroc=pair_auroc,
            spearman_table=spearman_report["table"],
            model_pack_report=model_report,
            group_stats=group_stats,
            log=True,
        )
    elif log and hi_pr_rho is not None:
        print_hi_pr_agreement(df, log=True)

    return FourRegionAnalysis(
        df=df,
        plot_paths=plot_paths,
        group_stats=group_stats,
        auroc_ranking=auroc_ranking,
        mean_diff=mean_diff,
        pair_auroc=pair_auroc,
        takeaway_lines=takeaway_lines,
        pairwise_takeaway=pair_line,
        signal_group_confusion=signal_cm_report["confusion_table"],
        model_pack_report=model_report,
        class_diagnostics=class_diagnostics,
        spearman_report=spearman_report,
        hi_pr_rho=hi_pr_rho,
    )


__all__ = ["FourRegionAnalysis", "analyze_four_region_run"]
