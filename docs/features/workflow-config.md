# Workflow config map (wizard → YAML)

The progressive UI never builds flat training dicts on the hot path. It edits a **`workflow`** session dict; [`run_spec.build_run_yaml(workflow)`](../../src/uqlab_orchestrator/run_spec.py) produces nested YAML for [`pipeline.run`](../../src/uqlab/runner/pipeline.py).

## Step 1 — Dataset

| Wizard (`workflow`) | YAML (`data`) |
|---------------------|---------------|
| `dataset_config.dataset_name` | `data.dataset_name` |
| `dataset_config.noise_type` | `data.noise_type` |
| `dataset_config.stats` | (not in YAML — UI only) |

## Step 2 — Training

| Wizard | YAML |
|--------|------|
| `training_config.model_architecture` | `model.architecture` |
| `training_config.hidden_dim` | `model.hidden_dim` |
| `training_config.dropout` | `model.dropout` |
| `training_config.epochs` | `training.epochs` |
| `training_config.learning_rate` | `training.learning_rate` |
| `training_config.use_checkpoint` | `model.checkpoint_path` (when resuming) |

Scope is derived: ResNet/CNN → `head_only`; DINOv2 → `feature_space` unless end-to-end.

## Step 3 — Uncertainty / sweep axis

| Wizard | YAML |
|--------|------|
| `uncertainty_config.epistemic_enabled` | sets `data.under_train_per_class` sweep vs single point |
| `uncertainty_config.under_train_per_class` | `data.under_train_per_class` |
| `uncertainty_config.regular_train_per_class` | `data.regular_train_per_class` |
| `uncertainty_config.under_supported` | `data.under_supported_classes` |
| `uncertainty_config.aleatoric_enabled` | label-noise sweep vs clean |
| `uncertainty_config.custom_noise_rate` | `data.aleatoric_noise_percentage` |
| `uncertainty_config.sweep_mode` | selects points in `generate_sweep_runs` |

Sweep expansion: [`generate_sweep_runs`](../../src/uqlab_orchestrator/run_spec.py) — not in the wizard dict directly.

## Step 4 — Evaluation

| Wizard | YAML |
|--------|------|
| `evaluation_config.eval_per_group` | `data.eval_per_group` |
| `evaluation_config.mc_passes` | `evaluation.mc_passes` |
| `evaluation_config.signals` (families) | `evaluation.signals` |

Signal families (strategy): predictive / logit / attribution — see [`shared/config/signals.py`](../../src/uqlab/shared/config/signals.py).

## Step 5 — Launch

| Action | Code |
|--------|------|
| Build configs | `generate_sweep_configs(workflow)` |
| POST to API | `launch_workflow_experiments(workflow, auto_start=…)` |
| Backend train | `DirectExecutor` → `pipeline.run` |

### Launch modes (progressive UI)

Step 5 and sidebar **Quick launch** expose the same four actions. Paper reproduction is **two separate 1D sweeps**, not one 2D grid.

| Mode | What runs | Swept axis | Fixed axis (from Step 3 or paper default) |
|------|-----------|------------|-------------------------------------------|
| **Custom sweep** | N runs from Step 3 `sweep_enabled` + `sweep_kind` | Label noise *or* under-train (one axis) | Other uncertainty type off or fixed |
| **Fig 3** | Under-train campaign | `under_train_per_class` grid | Label noise / epistemic settings mirrored from workflow |
| **Fig 4** | Label-noise campaign | `label_noise_percent` grid | Under-train mirrored from workflow |
| **Both figures** | Fig 3 campaign then Fig 4 (`2N` runs, two sweep groups) | Each campaign sweeps one axis | See preview expander in launch cards |

Code paths:

- Custom: `launch_workflow_experiments(workflow)`
- Fig 3: `launch_paper_profile(workflow, "under_train")`
- Fig 4: `launch_paper_profile(workflow, "noise")`
- Both: `launch_paired_paper_profiles(workflow)`

Preview helper: `paper_sweep_preview(workflow, profile)` in [`validation_config.py`](../../src/uqlab_orchestrator/config/validation_config.py).  
UI: [`sweep_launch_cards.py`](../../src/uqlab/ui_components/progressive/sweep_launch_cards.py).

## Sweep grouping (results)

After launch, experiments are grouped by:

1. `sweep_group_id` metadata (if present)
2. Name pattern `prefix_timestamp_param_value`
3. Single-parameter config diff

See [`sweep-grouping.md`](sweep-grouping.md) and [`sweep_groups.py`](../../src/uqlab_orchestrator/sweep_groups.py).

## Related

- [`START_HERE.md`](../../START_HERE.md)
- [`src/uqlab/runner/README.md`](../../src/uqlab/runner/README.md)
