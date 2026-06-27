# Evaluation Pipeline

**Date**: 2026-06-24 (updated after naming refactor)
**Purpose**: Accurate map of the experiment evaluation pipeline and where its code lives.

> Renamed from the repo-root `EVALUATION_STRUCTURE_ANALYSIS.md`. The `fast_pilot_*`
> modules/symbols and the monolithic `evaluator.py` were renamed/split in 2026-06-24
> (see "Naming changes" below). On-disk artifact names (e.g. `zwischen/`) are unchanged.

---

## Executive Summary

1. **Evaluation runs inside `run_experiment_core`** — same process as training, not a separate CLI step.
2. **Signal computation and AUROC scoring are modular** (`experiment_eval.py`, `metrics.py`, signals registry).
3. **`run_experiment_core` reads as phases** — private phase helpers + a removed duplicate `persist_experiment_summaries` call. No public API or artifact format changed by the refactor.

---

## 1. End-to-end flow

```
scripts/runners/run_fast_uncertainty_classification.py  (CLI)
    ↓
runner/execute.run_from_yaml()
    ↓
runner/experiment_core.run_experiment_core()
    ↓ [setup]      prepare_experiment_data → _prepare_eval_data_and_model
    ↓ [train]      train_feature_model / train_image_model
    ↓ [post-train] save_training_data_csv, save_interim (zwischen/)
    ↓ [signals]    runner.phases.eval.collect_uncertainty_signals
    ↓ [score]      runner.phases.eval.score_uncertainty_signals
    ↓ [summary]    _build_run_summary → persist_experiment_summaries (once)
    ↓ [export]     checkpoint.pt, results.pt (_export_run_results), console AUROC tables
```

Evaluation is **not** a separate job. It starts after `model.eval()` in the same function that trained the model.

---

## 2. Module map

| Module | Role | Notes |
|--------|------|-------|
| [`runner/experiment_core.py`](../../src/uqlab/runner/experiment_core.py) | Orchestrator (`run_experiment_core`) | Phase helpers below |
| [`runner/phases/eval.py`](../../src/uqlab/runner/phases/eval.py) | Signal collection + AUROC scoring | Runner phase |
| [`evaluation/metrics/scoring.py`](../../src/uqlab/evaluation/metrics/scoring.py) | AUROC math, confusion matrix, signal classifiers | Pure computation |
| [`evaluation/reporting/result_writers.py`](../../src/uqlab/evaluation/reporting/result_writers.py) | `summary.json`/`summary.md`/CSV output, `persist_experiment_summaries` | File/format output |
| [`evaluation/metrics/artifacts.py`](../../src/uqlab/evaluation/metrics/artifacts.py) | `results.pt` read contract (`EvalRunArtifacts`) | Consumed by plots/API/bridge |
| [`data/setup.py`](../../src/uqlab/data/setup.py) | Load dataset + build train/eval splits | Data phase |
| [`evaluation/signals/sources.py`](../../src/uqlab/evaluation/signals/sources.py) | Signal source wiring | Clean |
| [`evaluation/signals/registry.py`](../../src/uqlab/evaluation/signals/registry.py) | Metric definitions | Clean |

`metrics.py` + `result_writers.py` replace the former monolithic `evaluator.py` (math vs. I/O, split with no cross-dependencies). There is still no standalone `EvaluationCoordinator` class; phase helpers were chosen over a larger architectural split.

---

## 3. `run_experiment_core` phase helpers

Private functions in [`experiment_core.py`](../../src/uqlab/runner/experiment_core.py):

| Helper | Phase |
|--------|-------|
| `_prepare_eval_data_and_model` | Embeddings/images packs, `build_model`, checkpoint resume |
| `_build_run_summary` | `eval_protocol`, signal formulas, `summary` dict |
| `_export_run_results` | `results.pt` for sweep pools and downstream consumers |
| `_print_auroc_tables` | Console AUROC grouped by signal family |

`run_experiment_core` now reads as a linear phase sequence instead of one undifferentiated block.

### Bug fixed: duplicate persist

`persist_experiment_summaries(...)` was previously called **twice** with identical arguments — once after building `summary`, again after console printing. The `summary` dict was never mutated between calls, so the second write was redundant. **Only the first call remains** (kept early so `summary.json` survives if later export steps fail).

---

## 4. What evaluation does (three steps)

### Phase A — Signal collection

**File**: [`runner/phases/eval.py`](../../src/uqlab/runner/phases/eval.py) — `collect_uncertainty_signals`

- MC dropout (if enabled)
- Attribution signals (DualXDA, EK-FAC, GradDot)
- Predictive uncertainty (entropy, mutual information)
- Returns `signal_table: dict[signal_name → tensor[N_eval]]`

### Phase B — Signal scoring

**File**: [`evaluation/pipeline/experiment_eval.py`](../../src/uqlab/evaluation/pipeline/experiment_eval.py) — `score_uncertainty_signals`

- One-vs-rest AUROC per signal (aleatoric / epistemic / OOD), via `metrics.py`
- Writes `per_sample_signals.csv` (`result_writers.save_per_sample_csv`)
- Returns `auroc_rows`, `one_vs_rest_auroc`, `clf_rows`

### Phase C — Persistence

**File**: [`evaluation/result_writers.py`](../../src/uqlab/evaluation/result_writers.py) — `persist_experiment_summaries`

- `summary.json`, `summary.md`
- Called **once** per run from `run_experiment_core`

Additional artifacts written in the orchestrator (not in `result_writers.py`):

- `training_data.csv`, `zwischen/` (interim stage artifacts), `checkpoint.pt`, `results.pt`, `signal_formula_manifest.json`

> `zwischen/` (German "interim") is the on-disk interim-artifact directory consumed by
> run recovery (`zwischen_finalize` tier). The name is a persisted contract and is kept as-is.

---

## 5. Documentation index

| Doc | Focus |
|-----|-------|
| [`docs/UQLAB_FLOW.md`](../UQLAB_FLOW.md) | System overview + artifact contract |
| [`docs/features/evaluation-protocol.md`](../features/evaluation-protocol.md) | Evaluation methodology |
| [`src/uqlab/evaluation/README.md`](../../src/uqlab/evaluation/README.md) | Package overview |
| [`docs/debug/EVAL_ARTIFACTS.md`](../debug/EVAL_ARTIFACTS.md) | Output files |

---

## 6. Answers to common questions

### Is evaluation well-structured?

**Mostly at the module level, improving at the orchestrator level.**

- **Works well**: signal registry, `experiment_eval` collect/score split, AUROC math (`metrics.py`), artifact contents.
- **Was awkward**: monolithic `run_experiment_core`, duplicate persist call (fixed), mixed metrics+I/O in `evaluator.py` (split into `metrics.py` + `result_writers.py`).
- **Deferred**: standalone evaluation coordinator callable without training.

### Is evaluation after `run_fast_uncertainty`?

**It is inside it.** The CLI script calls `pipeline.run()` → `run_experiment_core()`. Training finishes first; evaluation runs in the same function before return.

---

## 7. Naming changes (2026-06-24)

| Old | New |
|-----|-----|
| `runner/fast_pilot_core.py` | `runner/experiment_core.py` |
| `evaluation/pipeline/fast_pilot_eval.py` | `evaluation/pipeline/experiment_eval.py` |
| `data/fast_pilot_loader.py` | `data/experiment_loader.py` |
| `evaluation/benchmarks/disentangling/fast_pilot.py` | `.../disentangling/experiment.py` |
| `evaluation/evaluator.py` (monolith) | `evaluation/metrics.py` + `evaluation/result_writers.py` |
| `prepare_fast_pilot_data` / `FastPilotDataContext` | `prepare_experiment_data` / `ExperimentDataContext` |
| `sample_indices_for_fast_pilot` | `sample_indices_for_experiment` |
| `FastPilotDisentanglingModel` | `ExperimentDisentanglingModel` |
| `build_fast_pilot_signal_table` | `build_experiment_signal_table` |
| `compute_eval_signals` / `summarize_eval_signals` (aliases) | dropped — use `collect_uncertainty_signals` / `score_uncertainty_signals` |
| `_load_packs_and_build_model` / `_save_results_pt` | `_prepare_eval_data_and_model` / `_export_run_results` |

Kept as-is (persisted/wire contracts): the `zwischen/` dir + `zwischen_finalize` recovery tier, the `"ekfac_fast_pilot"` scores name, and the `run_fast_uncertainty_classification.py` CLI filename.

---

## 8. Future work (optional, not started)

1. Extract `evaluate_uncertainty_signals(model, eval_inputs, ...)` as a public seam in `evaluation/pipeline/` so evaluation can run without training.
2. Structured phase logging (beyond existing `# ===` comment banners).

---

**Status**: Refactor complete. Behavior and artifact formats unchanged.
