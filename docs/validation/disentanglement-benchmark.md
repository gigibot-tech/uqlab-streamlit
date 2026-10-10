# Disentanglement benchmark (paper metric)

**Flow →** [`docs/UQLAB_FLOW.md`](../UQLAB_FLOW.md)

Upstream package: [ivopascal/disentanglement_error](https://github.com/ivopascal/disentanglement_error) — vendored under `src/uqlab/vendor/disentanglement_error/` (see `UPSTREAM.md`).

## Two phases (training vs analysis)

| Phase | Entry | Config | Output |
|-------|-------|--------|--------|
| **Train** | `scripts/runners/run_fast_uncertainty_classification.py` or API launch | `ExperimentConfig` YAML (`config.yaml`) | `results.pt`, `summary.json`, … |
| **Analyze** | `scripts/analysis/disentanglement_error.py` | Finished run dir / campaign run IDs | CSV scores, paper curves, optional PNGs |

Disentanglement is **post-hoc**: it reads uncertainty vectors from `results.pt`. It does not train models or call `model.fit()`.

## Training (ExperimentConfig)

Run a sweep point (or four-region experiment) like any other job:

```bash
PYTHONPATH=src python scripts/runners/run_fast_uncertainty_classification.py \
  --config configs/experiment/four_region.yaml \
  --output_dir results/my_run
```

Paper sweeps from Streamlit use `uqlab_orchestrator.disentanglement_launcher` → `experiment_launcher` → API → `DirectExecutor` → `run_from_yaml` (same `ExperimentConfig` path).

## Analysis CLI

### Score one finished run

```bash
PYTHONPATH=src python scripts/analysis/disentanglement_error.py score \
  --results-dir data/experiments/<run_id>/results \
  --mode paper \
  --output disentanglement_score.csv
```

Uses `score_bridge_pair_with_vendor_metric` from `uqlab.evaluation.benchmarks.disentangling.bridge_sweep` (reads `results.pt`, no re-training).

### Paper curves from a campaign

```bash
PYTHONPATH=src python scripts/analysis/disentanglement_error.py curves \
  --run-ids run_a,run_b,run_c \
  --sweep-kind label_noise \
  --plot \
  --out-dir results/disentanglement_curves
```

Builds the three-line plot (accuracy + global aleatoric + global epistemic vs `Percentage`) via `build_paper_benchmark_plot` — same series semantics as `json_results_to_df`, but sourced from on-disk campaign runs instead of the removed vendor `fit()` sweep.

## Architecture

| Layer | Role |
|-------|------|
| `uqlab_orchestrator.disentanglement_launcher` | Primary launch — workflow → per-point `build_run_yaml` + API |
| `uqlab.evaluation.pipeline.campaign_score` | Aggregate `results.pt` → paper `ExperimentResults` |
| `uqlab.evaluation.pipeline.paper_benchmark_plot` | Three-line plot payload from campaign runs |
| `uqlab.evaluation.benchmarks.disentangling.ExperimentDisentanglingModel` | **`results.pt` reader** — `predict_disentangling` extracts signal columns |
| `uqlab.vendor.disentanglement_error` | Vendor metric (`calculate_disentanglement_error`) on precomputed vectors |
| `uqlab.runner.execute` | Single-run training engine |

Default uncertainty pairing (`predict_mode="paper"`):

- aleatoric ← `expected_entropy`
- epistemic ← `mutual_info`

Signal presets: `signal` / `signal_dualxda`, `signal_ek_fak`. Override with `aleatoric_signal` / `epistemic_signal`.

`predict_disentangling` does **not** run MC or attribution — those must be enabled during the training job. See `uqlab.shared.config.signals` (`PREDICT_DISENTANGLING_NOTE`, `bridge_job_requirements`).

## Paper plots vs uqlab sweep plots

| Aspect | Paper plot (`paper_benchmark_plot`) | uqlab sweep line plot |
|--------|-------------------------------------|------------------------|
| Data | Global means from `predict_disentangling` | Pool-filtered means from `results.pt` |
| X axis | `Percentage` 0–1 | `noise_percent` or `under_train_per_class` |
| Y curves | scores + aleatorics + epistemics | One signal + accuracy per pool |
| UI | `paper_benchmark_plot_viz.py` | `sweep_line_plot_viz.py` |
| CLI | `scripts/analysis/disentanglement_error.py curves --plot` | — |

## Script layout

```
scripts/runners/     ExperimentConfig → run_from_yaml
  run_fast_uncertainty_classification.py   (default config: four_region.yaml)
  run_validation_experiments.py            (sweep orchestrator)
  run_fast.py                              (wrapper)

scripts/analysis/    post-hoc (no training)
  disentanglement_error.py                 (score + curves)
  four_region_validation.py                (correlation report)
  paper_benchmarks.py                      (Keras paper CSV flatten)
```

## Tests

- `tests/test_disentangling_model.py` — `ExperimentDisentanglingModel`, `json_results_to_df`
- `tests/test_campaign_paper_score.py` — aggregate mock `results.pt` → paper point
- `tests/test_paper_benchmark_plot.py` — campaign → plot payload, correlations
