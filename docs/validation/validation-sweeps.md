# Validation sweeps

Hyperparameter sweeps validate that uncertainty **signals track** controlled data axes. All sweeps call the same single-run engine (`experiment_core` → `collect_uncertainty_signals` → `score_uncertainty_signals`); only the YAML data geometry changes per point.

Metrics come from [`signals/catalog.py`](../../src/uqlab_core/evaluation/signals/catalog.py) (metadata) and [`signals/registry.py`](../../src/uqlab_core/evaluation/signals/registry.py) (compute), scored in [`scoring.py`](../../src/uqlab_core/evaluation/scoring.py).

## Two sweep families

### Legacy paper sweeps (`partition_mode: legacy`)

| UI / code name | Swept YAML field | Typical grid | Output |
|----------------|------------------|--------------|--------|
| `label_noise`, `noise_rate` | `data.aleatoric_noise_percentage` | 0–100% | `results/validation/label_noise_sweep/metrics.csv` |
| `under_train`, `dataset_size` | `data.under_train_per_class` | fraction grid | `results/validation/dataset_size_sweep/metrics.csv` |

**Orchestrators:**

- [`uqlab_orchestrator/config/validation_config.py`](../../src/uqlab_orchestrator/config/validation_config.py) — grid definitions
- [`uqlab_orchestrator/run_spec.py`](../../src/uqlab_orchestrator/run_spec.py) — `generate_sweep_runs()`
- [`scripts/runners/run_validation_experiments.py`](../../scripts/runners/run_validation_experiments.py) — CLI batch runner

Global noise applies to loader-level label corruption; epistemic arm uses `under_supported_classes` + `under_train_per_class`.

### Four-region sweeps (`partition_mode: four_region`)

| Sweep kind | Swept field | Grid (`four_region_validation.py`) | Output |
|------------|-------------|-------------------------------------|--------|
| `noise_sweep` | `class_regions.noisy.label_flip_pct` | 0, 10, 25, 50, 75, 100 | `results/validation/four_region/noise_sweep/noise{pct}/` |
| `sparsity_sweep` | `class_regions.sparse.train_fraction` | 1, 5, 10, 25, 50, 100 (%) | `results/validation/four_region/sparsity_sweep/sparse{pct}/` |

Constants: `NOISE_SWEEP_PCTS`, `SPARSITY_SWEEP_PCTS` in [`four_region_validation.py`](../../src/uqlab/evaluation/validation/four_region_validation.py).

Only the noisy or sparse region spec changes per point; clean/OOD blocks stay at preset defaults.

## Vocabulary map

| Name in UI/docs | Same as | Meaning |
|-----------------|---------|---------|
| `label_noise` | `noise_rate` | Legacy global aleatoric sweep |
| `under_train` | `dataset_size` | Legacy global epistemic sweep |
| `noise_sweep` | `noise_percent` (CSV) | Four-region noisy `label_flip_pct` sweep |
| `sparsity_sweep` | `sparse_fraction` | Four-region sparse `train_fraction` sweep |

## Metric path (every sweep point)

```
build_run_data (split + noise per YAML)
  → train_classifier
  → collect_uncertainty_signals  # sources → PrimitiveStore → signal_table
  → score_uncertainty_signals    # AUROC, per_sample_signals.csv
  → metrics row (CSV or four_region_metrics.json)
```

## Notebook benchmark is not a sweep

[`four_region_benchmark.ipynb`](../../notebooks/four_region_benchmark.ipynb) runs **one** YAML point per dataset (30% flip, 10% sparse). Use `four_region_validation` for systematic grids.

## Related

- [`four-region-partition.md`](four-region-partition.md) — where split/noise happen in `/data`
- [`evaluation-pipeline.md`](evaluation-pipeline.md) — collect vs score
- [`disentanglement-benchmark.md`](disentanglement-benchmark.md) — paper Fig 3/4 interpretation
