"""
Step~6 metrics aligned with ``docs/features/four-region-step6-synthesis.tex``.

Use ``report_profile="synthesis"`` on :func:`analyze_four_region_run` (or pass
``log_profile="synthesis"`` to individual reporters) to log only headline tables;
``report_profile="full"`` keeps exploratory diagnostics (all pairwise axes, all
Spearman slices/targets, class ECDFs).
"""

from __future__ import annotations

from typing import Any, Literal, Sequence

import pandas as pd
from scipy import stats

from uqlab_core.evaluation.reporting.attribution_distribution_summary import (
    DEFAULT_FOUR_REGION_PAIRWISE,
    DIST_SIGNAL_COLS,
)
from uqlab_core.evaluation.reporting.signal_spearman_diagnostics import (
    TASK2_TARGETS as _TASK2_TARGETS,
)

ReportProfile = Literal["synthesis", "full"]

# --- Task 1 (pool AUROC) -----------------------------------------------------

SYNTHESIS_PRIMARY_PAIR = "noisy_vs_sparse"

SYNTHESIS_AUX_PAIRS: tuple[tuple[str, str], ...] = (
    ("noisy_vs_sparse", "expected_entropy"),
    ("sparse_minus_ood", "inverse_coherence_dualxda"),
    ("clean_minus_ood", "attribution_participation_dualxda"),
)

SYNTHESIS_POOL_SIGNALS: tuple[str, ...] = (
    "attribution_participation_dualxda",
    "attribution_entropy_dualxda",
    "coherence_dualxda",
    "mutual_info",
    "expected_entropy",
    "inverse_coherence_dualxda",
)

SYNTHESIS_PAIR_LABELS: tuple[str, ...] = tuple(
    dict.fromkeys([SYNTHESIS_PRIMARY_PAIR, *(p for p, _ in SYNTHESIS_AUX_PAIRS)])
)

# --- Task 2 (graded severity, Appendix B) ------------------------------------

SYNTHESIS_TASK2_SLICE = "noisy_region"
SYNTHESIS_TASK2_TARGETS: tuple[str, ...] = _TASK2_TARGETS
SYNTHESIS_TASK2_SIGNALS: tuple[str, ...] = (
    "attribution_entropy_dualxda",
    "attribution_participation_dualxda",
)

# --- Plots -------------------------------------------------------------------

SYNTHESIS_PLOT_SIGNALS: tuple[str, ...] = (
    "attribution_entropy_dualxda",
    "attribution_participation_dualxda",
    "coherence_dualxda",
    "mutual_info",
)


def is_synthesis_profile(profile: str | None) -> bool:
    return str(profile or "synthesis").strip().lower() != "full"


def synthesis_plot_metrics(
    *,
    enable_graddot: bool = False,
    enable_ek_fac: bool = False,
) -> list[str]:
    """Box plots for headline Step~6 signals (H, PR, coherence, mutual_info)."""
    from uqlab_core.evaluation.signals.catalog import AttributionBackend

    metrics = list(SYNTHESIS_PLOT_SIGNALS)
    if enable_ek_fac:
        metrics.append(f"coherence_{AttributionBackend.EK_FAK.value}")
    if enable_graddot:
        metrics.append(f"coherence_{AttributionBackend.GRADDOT.value}")
    return metrics


def synthesis_pairwise_pairs() -> list[tuple[str, str, str]]:
    labels = set(SYNTHESIS_PAIR_LABELS)
    return [triple for triple in DEFAULT_FOUR_REGION_PAIRWISE if triple[0] in labels]


def synthesis_contrast_cols(
    df: pd.DataFrame,
    *,
    extra: Sequence[str] | None = None,
) -> list[str]:
    """Signal columns for AUROC / Spearman exports in synthesis mode."""
    candidates = [
        *SYNTHESIS_POOL_SIGNALS,
        *DIST_SIGNAL_COLS,
        *(extra or ()),
    ]
    return list(dict.fromkeys(c for c in candidates if c in df.columns))


def print_hi_pr_agreement(df: pd.DataFrame, *, log: bool = True) -> float | None:
    """Spearman ρ(H_i, PR_i) over all eval rows (synthesis §5.2 / tab:h-pr)."""
    hi = "attribution_entropy_dualxda"
    pr = "attribution_participation_dualxda"
    if hi not in df.columns or pr not in df.columns:
        return None
    sub = df[[hi, pr]].dropna()
    if len(sub) < 5:
        return None
    rho = float(stats.spearmanr(sub[hi], sub[pr]).statistic)
    if log:
        print(f"\nWidth agreement: ρ(H_i, PR_i) = {rho:.2f}  (n={len(sub)})")
    return rho


def coherence_from_inverse_coherence(series: pd.Series) -> pd.Series:
    r"""$C_i^{(k)} = 1 - U_i^{\mathrm{coh}}$ from stored ``inverse_coherence_*`` column."""
    return 1.0 - pd.to_numeric(series, errors="coerce")


def print_synthesis_pool_auroc(pair_auroc: pd.DataFrame, df: pd.DataFrame | None = None) -> None:
    """Headline + auxiliary pool AUROC lines from tab:pool-auroc / tab:aux-contrasts."""
    if pair_auroc.empty:
        print("\nSynthesis pool AUROC: (no rows)")
        return

    print("\nSynthesis pool AUROC (Task~1 + selected aux axes):")
    if SYNTHESIS_PRIMARY_PAIR in pair_auroc.index:
        row = pair_auroc.loc[SYNTHESIS_PRIMARY_PAIR]
        print(f"  [{SYNTHESIS_PRIMARY_PAIR}]")
        width_signals = (
            "attribution_participation_dualxda",
            "attribution_entropy_dualxda",
            "mutual_info",
        )
        for signal in (
            *width_signals,
            "coherence_dualxda",
            "inverse_coherence_dualxda",
        ):
            col = signal
            if col not in pair_auroc.columns:
                short = "coherence" if signal == "coherence_dualxda" else None
                if short and short in pair_auroc.columns:
                    col = short
                else:
                    continue
            val = row.get(col)
            if pd.notna(val):
                label = "coherence_dualxda" if signal == "coherence_dualxda" else signal
                print(f"    {label:38s}  {float(val):.3f}")

        for pair, signal in SYNTHESIS_AUX_PAIRS:
            if pair != SYNTHESIS_PRIMARY_PAIR:
                continue
            if signal not in pair_auroc.columns:
                continue
            val = row.get(signal)
            if pd.notna(val):
                print(f"    {signal:38s}  {float(val):.3f}")

    for pair, signal in SYNTHESIS_AUX_PAIRS:
        if pair == SYNTHESIS_PRIMARY_PAIR:
            continue
        if pair not in pair_auroc.index or signal not in pair_auroc.columns:
            continue
        val = pair_auroc.loc[pair, signal]
        if pd.notna(val):
            print(f"  [{pair}] {signal}: {float(val):.3f}")


def print_synthesis_backend_coh(pair_auroc: pd.DataFrame) -> None:
    """``noisy_vs_sparse`` inverse_coherence per backend (tab:backend-coh)."""
    if SYNTHESIS_PRIMARY_PAIR not in pair_auroc.index:
        return
    row = pair_auroc.loc[SYNTHESIS_PRIMARY_PAIR]
    backends = (
        ("inverse_coherence_dualxda", "DualXDA"),
        ("inverse_coherence_ek_fak", "EK-FAC"),
        ("inverse_coherence_graddot", "GradDot"),
    )
    hits = [
        (label, float(row[col]))
        for col, label in backends
        if col in pair_auroc.columns and pd.notna(row.get(col))
    ]
    if not hits:
        return
    print("\nBackend check (noisy_vs_sparse inverse_coherence):")
    for label, val in hits:
        print(f"  {label:8s}  {val:.3f}")


def _pairwise_auroc_on_df(df: pd.DataFrame, scores: pd.Series, pair_label: str) -> float | None:
    from uqlab_core.evaluation.scoring import binary_auroc_vs_group
    from uqlab_core.run_artifacts import GROUP_NAMES
    import torch

    lookup = {v: k for k, v in GROUP_NAMES.items()}
    triple = next((t for t in synthesis_pairwise_pairs() if t[0] == pair_label), None)
    if triple is None:
        triple = next((t for t in DEFAULT_FOUR_REGION_PAIRWISE if t[0] == pair_label), None)
    if triple is None:
        return None
    _, left, right = triple
    return binary_auroc_vs_group(
        torch.tensor(scores.astype(float).values),
        torch.tensor(df["group"].map(lookup).values),
        positive_group=int(lookup[left]),
        negative_group=int(lookup[right]),
    )


def print_synthesis_task2(spearman_table: pd.DataFrame) -> None:
    """Task~2 rows only (noisy_region × label_disagreement / noisy_support_ratio)."""
    if spearman_table.empty:
        print("\nSynthesis Task~2: (no rows)")
        return

    print(
        f"\nSynthesis Task~2 (graded severity, slice={SYNTHESIS_TASK2_SLICE!r}; "
        f"see Appendix B for target definitions):"
    )
    for signal, target in (
        (SYNTHESIS_TASK2_SIGNALS[0], SYNTHESIS_TASK2_TARGETS[0]),
        (SYNTHESIS_TASK2_SIGNALS[1], SYNTHESIS_TASK2_TARGETS[1]),
    ):
        row = spearman_table[
            (spearman_table["slice"] == SYNTHESIS_TASK2_SLICE)
            & (spearman_table["signal"] == signal)
            & (spearman_table["target"] == target)
            & spearman_table["stratify_clean_label"].isna()
        ]
        if row.empty:
            print(f"  {signal} × {target}: —")
            continue
        hit = row.iloc[0]
        if pd.notna(hit.get("skip_reason")):
            print(f"  {signal} × {target}: skipped ({hit['skip_reason']})")
        else:
            print(
                f"  {signal} × {target}: ρ={float(hit['rho']):+.2f}  "
                f"(n={int(hit['n'])})"
            )


def print_synthesis_pack_accuracy(accuracy_table: pd.DataFrame) -> None:
    """Partition setup verification from tab:model-acc."""
    if accuracy_table.empty or "group" not in accuracy_table.columns:
        return
    by_group = accuracy_table.set_index("group")["accuracy"].to_dict()
    epi = by_group.get("epistemic_like")
    ale = by_group.get("aleatoric_like")
    clean = by_group.get("clean")
    ood = by_group.get("ood_like")
    print("\nPartition setup verification (classifier accuracy by eval pack):")
    for name in ("clean", "aleatoric_like", "epistemic_like", "ood_like"):
        if name in by_group:
            row = accuracy_table.loc[accuracy_table["group"] == name].iloc[0]
            n = int(row.get("n", 0))
            correct = int(row.get("correct", round(float(by_group[name]) * n)))
            print(f"  {name:16s}  {100 * float(by_group[name]):.1f}%  ({correct}/{n})")
    if epi is not None and ale is not None:
        print(f"  epistemic − aleatoric:  {100 * (float(epi) - float(ale)):+.1f} pp")
    if clean is not None and ood is not None:
        print(f"  clean − ood:            {100 * (float(clean) - float(ood)):+.1f} pp")


def print_synthesis_step6_summary(
    *,
    df: pd.DataFrame,
    pair_auroc: pd.DataFrame,
    spearman_table: pd.DataFrame,
    model_pack_report: dict[str, Any],
    group_stats: pd.DataFrame | None = None,
    log: bool = True,
) -> None:
    """Compact log block matching the synthesis document tables."""
    if not log:
        return

    print("\n" + "=" * 60)
    print("Step 6 synthesis summary (four-region-step6-synthesis.tex)")
    print("=" * 60)

    if group_stats is not None and not group_stats.empty:
        headline = (
            "attribution_entropy_dualxda",
            "attribution_participation_dualxda",
            "coherence_dualxda",
            "mutual_info",
        )
        pack_means = df.groupby("group")[list(headline)].mean()
        if (
            "aleatoric_like" in pack_means.index
            and "epistemic_like" in pack_means.index
        ):
            print("\nPack means (aleatoric − epistemic):")
            labels = {
                "attribution_entropy_dualxda": "ΔH",
                "attribution_participation_dualxda": "ΔPR",
                "coherence_dualxda": "ΔC",
                "mutual_info": "ΔMI",
            }
            for col in headline:
                if col not in pack_means.columns:
                    continue
                delta = (
                    float(pack_means.loc["aleatoric_like", col])
                    - float(pack_means.loc["epistemic_like", col])
                )
                print(f"  {labels[col]}: {delta:+.3f}")

    print_hi_pr_agreement(df, log=True)
    print_synthesis_pool_auroc(pair_auroc, df=df)
    print_synthesis_backend_coh(pair_auroc)
    print_synthesis_task2(spearman_table)
    print("=" * 60)
    print(
        "Task~2 targets (Appendix B): label_disagreement = supporter-label entropy; "
        "noisy_support_ratio = flip-cohort share among top-k supporters."
    )


__all__ = [
    "ReportProfile",
    "SYNTHESIS_AUX_PAIRS",
    "SYNTHESIS_PAIR_LABELS",
    "SYNTHESIS_PLOT_SIGNALS",
    "SYNTHESIS_POOL_SIGNALS",
    "SYNTHESIS_PRIMARY_PAIR",
    "SYNTHESIS_TASK2_SIGNALS",
    "SYNTHESIS_TASK2_SLICE",
    "SYNTHESIS_TASK2_TARGETS",
    "is_synthesis_profile",
    "print_hi_pr_agreement",
    "print_synthesis_backend_coh",
    "print_synthesis_pack_accuracy",
    "print_synthesis_pool_auroc",
    "print_synthesis_step6_summary",
    "print_synthesis_task2",
    "synthesis_contrast_cols",
    "synthesis_pairwise_pairs",
    "synthesis_plot_metrics",
]
