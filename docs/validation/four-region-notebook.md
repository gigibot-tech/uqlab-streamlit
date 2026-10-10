# Four-region benchmark notebook

Notebook: [`notebooks/four_region_benchmark.ipynb`](../../notebooks/four_region_benchmark.ipynb)

Six-step walkthrough (change `DATASET` in Step 1, Run All). Each step maps to a **`uqlab_core`** package.

| Step | Package | What | API |
|------|---------|------|-----|
| 1 | `uqlab_core.data` | Dataset + config | `load_classification_dataset`, `ExperimentConfig.from_yaml` |
| 2 | `uqlab_core.data` | **Split + noise** → tensor packs | `build_run_data` |
| 3 | `uqlab_core.models` | Train classifier | `train_classifier` |
| 4 | `uqlab_core.evaluation` | **Collect** vectors → scalars | `collect_uncertainty_signals` |
| 5 | `uqlab_core.evaluation` | **Score** scalars → AUROC/CSV | `score_uncertainty_signals` |
| 6 | analysis | Plots + tables (not in `summary.json`) | `four_region_reporting`, `attribution_distribution_summary` |

Same train/eval chain as [`experiment_core.py`](../../src/uqlab_core/runner/experiment_core.py) → [`train_eval.run_paper_experiment`](../../src/uqlab_core/runner/train_eval.py).

## Step 2 — data layer (partition lives here)

`build_run_data` reads YAML with `partition_mode: four_region` and applies:

- Noisy classes 0–3: 30% label flip
- Sparse 4–5: 10% train fraction
- Clean 6–7: full train
- OOD 8–9: withheld from training

See [`four-region-partition.md`](four-region-partition.md).

## Steps 4–5 — evaluation core

```python
# uqlab_core.evaluation.pipeline — collect (core vectors → signal_table)
eval_outputs = collect_uncertainty_signals(model, cfg, bundle, results_dir=run_dir, device=ctx.device)

# uqlab_core.evaluation.pipeline — score (AUROC → per_sample_signals.csv)
eval_summary = score_uncertainty_signals(eval_outputs, bundle, results_dir=run_dir, device=ctx.device, seed=ctx.seed)
```

Enable distribution signals in `cfg.evaluation.signals["attribution"]` before collect (Step 4).

## Step 6 — notebook analysis layer

- Box plots: `uqlab_core.evaluation.reporting.four_region_reporting`
- Distribution + pairwise tables: `uqlab.shared.notebook_utils.attribution_distribution_summary`

## Attribution toggles (Step 4)

- **DualXDA** — always on
- **GradDot** — `ENABLE_GRADDOT=True`
- **EK-FAC** — `ENABLE_EK_FAC=True` (requires `kronfluence`)

`apply_attribution_backends` from `uqlab_core.runner.notebook_run`.

## Sweeps vs this notebook

This notebook runs **one** YAML point. Systematic grids:

- Noise 0–100% on noisy region → [`four_region_validation.py`](../../src/uqlab/evaluation/validation/four_region_validation.py)
- Sparse 1–100% train fraction → same

See [`validation-sweeps.md`](validation-sweeps.md).

## Results

Default: `<repo>/results/four_region_benchmark/{fashion_mlp,cifar_resnet}/`

## Optional batch shortcut

`run_four_region_benchmark` runs both datasets without stepping through cells — see commented cell at notebook end.
