# Data pipeline

Single entrypoint for experiment data — mirrors the MLGym idea of one obvious call per task.

**Module README:** [`src/uqlab_core/data/README.md`](../../src/uqlab_core/data/README.md)

## The one call

```python
from uqlab.data import build_run_data  # → uqlab_core.data.build_run_data

bundle = build_run_data(config, project_root, seed=42, device=device)
```

Returns a `RunDataBundle`:

| Field | Type | Use |
|-------|------|-----|
| `dataset` | loaded train split | logging |
| `split_spec` | `SplitSpec` | eval group sizes, runner |
| `data_pack` | dict | `train_dataset`, eval packs, `mode`, `feature_dim` |
| `ctx` | `ExperimentDataContext` | config_view / banners |

Pass `bundle.data_pack` and `bundle.split_spec` to `run_paper_experiment` / `run_train_and_eval_phases`.

## Internal steps (do not call separately unless testing)

| Step | Function | Module |
|------|----------|--------|
| 1 | `step1_load_dataset_and_splits` | [`uqlab_core/data/buildData.py`](../../src/uqlab_core/data/buildData.py) |
| 2 | `step2_materialize_tensor_packs` | same |

Step 1: parse YAML data fields → `load_classification_dataset` → sample indices (legacy or four-region).

Step 2: resolve embeddings vs images mode → build train subset + four eval packs. Fails early with a clear message if DINOv2 weights are missing (embeddings mode).

## YAML fields → pipeline

```yaml
data:
  dataset_name: cifar10n
  noise_type: worse_label
  partition_mode: legacy          # or four_region
  under_supported_classes: [3, 5]
  regular_train_per_class: 300
  eval_per_group: 600
paths:
  data_root: ./data/cifar10n
  feature_cache_dir: ./cache/features
model:
  training_mode: feature_space    # or end_to_end
  architecture: dinov2_mlp
  dinov2_model: small
```

## Four-region partition

When `partition_mode: four_region`, class blocks and train/noise policies are defined in `data.class_regions`. Implementation: [`src/uqlab_core/data/splits/four_region.py`](../../src/uqlab_core/data/splits/four_region.py).

| Region | Classes (default) | Train policy | Eval `group` |
|--------|-------------------|--------------|--------------|
| Noisy | 0–3 | 30% label flip | `aleatoric_like` |
| Sparse | 4–5 | 10% train fraction | `epistemic_like` |
| Clean | 6–7 | full train | `clean` |
| OOD | 8–9 | no train | `ood_like` |

`build_run_data` forces global aleatoric noise off for four-region mode and applies flips only inside the noisy region.

Full bridge doc: [`four-region-partition.md`](four-region-partition.md).

## Dataset access

**Registry only:**

```python
from uqlab.data.datasets import load_classification_dataset, get_dataset_spec
```

Never import `uqlab.data.datasets.loaders.*` in application code.

## Runner integration

[`uqlab_core/runner/experiment_core.py`](../../src/uqlab_core/runner/experiment_core.py) calls `build_run_data` once before training.

## Related

- [`dataset-plugin.md`](dataset-plugin.md) — adding a new dataset via registry
- [`four-region-partition.md`](four-region-partition.md) — split → group → metrics
- [`validation-sweeps.md`](validation-sweeps.md) — noise/sparsity grids
- [`PAPER_FLOW.md`](PAPER_FLOW.md) — full paper API map
