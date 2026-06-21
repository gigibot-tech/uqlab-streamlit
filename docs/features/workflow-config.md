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

## Step 3 — Uncertainty / sweep perspective

Step 3 picks **one perspective** (`uncertainty_config.sweep_target`):

| `sweep_target` | Meaning | Step 3 shows |
|----------------|---------|--------------|
| `single` | Fixed training point | Epistemic + aleatoric |
| `label_noise` | Sweep Fig. 4 axis | Epistemic fixed mirror + noise grid |
| `under_train` | Sweep Fig. 3 axis | Aleatoric fixed mirror + under-train grid |
| `sweep_both` | Both axes swept (fine-grained) | Both grids in Step 3 — **one** launch button in Step 5 |

| Wizard | YAML |
|--------|------|
| `uncertainty_config.sweep_target` | UI launch perspective (maps to sweep fields) |
| `uncertainty_config.epistemic_enabled` | sets `data.under_train_per_class` sweep vs single point |
| `uncertainty_config.under_train_per_class` | `data.under_train_per_class` |
| `uncertainty_config.regular_train_per_class` | `data.regular_train_per_class` |
| `uncertainty_config.under_supported` | `data.under_supported_classes` |
| `uncertainty_config.aleatoric_enabled` | label-noise sweep vs clean |
| `uncertainty_config.custom_noise_rate` | `data.aleatoric_noise_percentage` |
| `uncertainty_config.sweep_mode` | quick/full grid for paper sweeps |

Sweep expansion: [`generate_sweep_runs`](../../src/uqlab_orchestrator/run_spec.py) — not in the wizard dict directly.

Preview helpers: `launch_mirror_preview`, `launch_button_labels` in [`validation_config.py`](../../src/uqlab_orchestrator/config/validation_config.py).

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
| Preflight | `assess_launch_readiness(workflow, experiments, project_root)` |
| Build configs | `expand_launch_candidates(workflow)` (arm-aligned, same as launch) |
| POST to API | `launch_primary_from_step3` / `launch_run_both` |
| Backend train | `DirectExecutor` → `pipeline.run` |

### Shared launch panel (Step 5 + sidebar)

Step 5 and sidebar **Quick launch** share one component: [`launch_panel.py`](../../src/uqlab/ui_components/progressive/launch_panel.py).

`streamlit_app_progressive.py` computes `assess_launch_readiness` **once per rerun** and passes the same `LaunchReadiness` to both surfaces. Layout differs only:

| Surface | Layout | Extra |
|---------|--------|-------|
| Sidebar | `compact` | Vertical buttons, shorter summary |
| Step 5 | `main` | Full width; optional `View full workflow state` expander |

**Panel order:**

1. One-line readiness summary
2. **Blocking** preflight only (`config_error` → Edit Step 3; `duplicate_ok` → Open Results) — hides launch row
3. **Launch row** — synced autostart + **Start sweep** / **Run both** (always opens confirm dialog)
4. **Suggested fix (optional)** expander below — resume sweep or plot-probe patch (not above launch buttons)

**Autostart:** single session key `launch_autostart` via [`launch_session.py`](../../src/uqlab/ui_components/progressive/launch_session.py) — sidebar, Step 5, and confirm dialog stay in sync.

**Confirm dialog:** every launch action (primary + Run both) shows arm preview, autostart toggle, and **Confirm launch** / **Cancel** before POST.

Launch buttons are **disabled** when `config_error` or `duplicate_ok`.

Code: [`launch_preflight.py`](../../src/uqlab_orchestrator/launch_preflight.py), UI [`launch_panel.py`](../../src/uqlab/ui_components/progressive/launch_panel.py), [`sweep_launch_cards.py`](../../src/uqlab/ui_components/progressive/sweep_launch_cards.py).

### Launch modes (perspective-first)

| Step 3 | Primary button | Run both |
|--------|----------------|----------|
| `single` | **Single run** | Mirror dialog: paired sweeps or single + complementary sweep |
| `label_noise` | **Start sweep (Fig. 4)** | **Run all (Fig. 3 + Fig. 4)** — preview then `launch_paired_paper_profiles` |
| `under_train` | **Start sweep (Fig. 3)** | **Run all (Fig. 3 + Fig. 4)** |
| `sweep_both` | **Launch both sweeps** (one button + confirm dialog) | — |

Code paths:

- Single: `launch_single_run(workflow)` (`sweep_enabled=false`)
- One-axis sweep: `launch_paper_profile(workflow, "noise" \| "under_train")`
- Run both (sweep_one): `launch_paired_paper_profiles(workflow)`
- Run both (single, mirror): `launch_run_both(workflow, mirror_mode=…)`

Paper reproduction = **one 1D sweep per registered perspective** under one campaign timestamp, not a 2D grid.

### Extensibility

Perspectives are defined in [`uncertainty/registry.py`](../../src/uqlab_orchestrator/uncertainty/registry.py).  
Mirroring is automatic: for primary P, **Run all** launches sweeps for all other **N−1** types via a for-loop over the registry.

**Adding a 3rd perspective:** append one `UncertaintyPerspective` to `UNCERTAINTY_PERSPECTIVES`, add sweep grids in `validation_config.py` if needed, and extend `arm_builder.build_arm_workflow` — Step 3 options, launch resolver, and Results arm tabs pick it up via `iter_perspectives()`.

Launch actions are resolved in [`launch_resolver.resolve_launch_actions`](../../src/uqlab_orchestrator/uncertainty/launch_resolver.py); UI renders buttons from that list (never hardcoded Fig 3/4 branches in `sweep_launch_cards.py`).

Arm workflows: [`arm_builder.py`](../../src/uqlab_orchestrator/uncertainty/arm_builder.py) (replaces inline profile `if` chains in the sidebar wrapper).

## Sweep grouping (results)

After launch, experiments are grouped by:

1. `sweep_group_id` metadata (if present)
2. Name pattern `prefix_timestamp_param_value`
3. Single-parameter config diff

When a campaign has both `fast_alea_*` and `fast_epis_*` runs, Results §2 offers **Noise sweep** | **Under-train sweep** tabs.

See [`sweep-grouping.md`](sweep-grouping.md) and [`sweep_groups.py`](../../src/uqlab_orchestrator/sweep_groups.py).

## Plot probe (duplicate-gated redo)

When **UI debug → plot probe redo suggestions** is on:

| Location | Gate | Ladder | On failure |
|----------|------|--------|------------|
| **Step 5 / sidebar** (optional expander) | `assess_launch_readiness` → resume or plot-probe suggestion | artifacts → completion (≥2 runs) → `build_sweep_line_plot` | **Suggested fix (optional)** below launch row: apply-only or **Apply suggested fix & launch** (respects `launch_autostart`) |
| **Results §2** | Plot render failed for selected campaign | Same ladder on campaign runs | Read-only status + **Review launch in Step 5** (no diff table, no launch buttons) |

Code: [`plot_probe/`](../../src/uqlab_orchestrator/plot_probe/), UI [`plot_probe_panel.py`](../../src/uqlab/ui_components/progressive/plot_probe_panel.py), preflight [`launch_preflight.py`](../../src/uqlab_orchestrator/launch_preflight.py).

Optional **Preflight detail (debug)** expander (both surfaces) shows diff table when `ui_debug.plot_probe_suggestions` is on.

Suggestions bias **upward** on `epochs`, `mc_passes`, `eval_per_group`, or `sweep_mode → full` (1–2 knobs per failure kind). No silent relaunch — user must **Apply** or **Apply & launch**.

### Training presets (`TRAINING_CONFIG`)

Step 3 sweep mode applies quick/full training presets to `training_config.epochs` and `evaluation_config.mc_passes`:

| Mode | Default epochs | MC passes |
|------|----------------|-----------|
| `quick` | 12 | 10 |
| `full` | 10 | 30 |

Defined in [`validation_config.py`](../../src/uqlab_orchestrator/config/validation_config.py); seeded into [`workflow_defaults.py`](../../src/uqlab_orchestrator/config/workflow_defaults.py).

## Related

- [`START_HERE.md`](../../START_HERE.md)
- [`src/uqlab/runner/README.md`](../../src/uqlab/runner/README.md)
