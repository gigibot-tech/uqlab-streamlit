---
name: ui-debug
description: >-
  Gate progressive Streamlit UI blocks with ui_debug.py. Use when adding or
  changing renderers in streamlit_app_progressive, results panels, workflow
  steps, or sidebar controls.
---
# UI debug (progressive app)

The progressive app hides UI blocks via toggles in [`src/uqlab/ui_components/ui_debug.py`](../../src/uqlab/ui_components/ui_debug.py). The debug panel lives in the **sidebar footer** via [`sidebar_controls.py`](../../src/uqlab/ui_components/selectors/sidebar_controls.py) → `render_ui_debug_panel()`.

## Mandatory checklist (new Streamlit block)

1. **Register** the key in `UI_DEBUG_REGISTRY` with a human label and default (`True` / `False`).
2. **Parent** — if nested, add `UI_DEBUG_PARENT[child] = parent`.
3. **Panel** — add the key to the right group in `UI_DEBUG_SECTIONS`.
4. **Gate** — wrap the renderer with `from uqlab.ui_components.ui_debug import ui_on` and `if not ui_on("key"): return` (or show a stub).
5. **Defaults version** — if you change defaults for existing keys, bump `UI_DEBUG_DEFAULTS_VERSION` and migrate in `init_ui_debug()`.

Never add a visible block without a registry key unless it is intentionally always-on infrastructure (e.g. `ensure_workflow_initialized`).

## Parent cascade

- `ui_on("child")` is `False` when **any ancestor** is off.
- Turning off a parent in the debug panel forces all descendants off (`_cascade_disable`, `_apply_parent_cascade_rules`).
- Do not rely on children staying on when the parent is off.

## Results section map (v4)

| UI block | Toggle key | Default |
|----------|------------|---------|
| Entire `## Results` | `results_section` | on |
| §1 Live status (header + bulk delete) | `results_live_status` | on |
| §1 Running progress bars | `results_running_progress` | off |
| §1 Auto-refresh checkbox | `results_auto_refresh_ui` | off |
| §1 5s JS auto-rerun | `results_auto_refresh_schedule` | off |
| §1 Bulk delete | `results_bulk_delete` | on (child of live status) |
| §2 Sweep analysis (3-line plots) | `results_sweep_analysis` | on |
| §3 Campaign expanders | `results_sweep_campaigns` | on |
| §3 Per-run details inside expanders | `results_experiment_details` | off |
| Standalone table | `results_standalone_table` | on |
| §4 Training data inspection | `results_training_data` | off |
| Footer status counts | `results_status_metrics` | on |

Entry point: [`results_section.py`](../../src/uqlab/ui_components/progressive/results_section.py) → [`experiment_results_panel.py`](../../src/uqlab/ui_components/results/experiment_results_panel.py).

When `results_section` is off, show a **visible stub** (caption), not a silent return.

When `results_section` is on but all sub-panels are off, show a **hint** pointing to UI debug.

## Launch / Step 5

| Block | Key | Parent |
|-------|-----|--------|
| Step 5 review summary | `step5_launch` | — |
| Launch cards (custom + Fig 3/4/both) | `step5_launch_cards` | `step5_launch` |
| Sidebar quick launch | `sidebar_paper_launch` | — |
| Launch result banner | `launch_result_banner` | — |

Shared component: [`sweep_launch_cards.py`](../../src/uqlab/ui_components/progressive/sweep_launch_cards.py).

## RESULTS_DEFAULTS_OFF

Keys in `RESULTS_DEFAULTS_OFF` stay **off** when the user clicks **Results defaults** in the debug panel. Add noisy or heavy panels here (per-run details, training data, auto-refresh).

## Auto-refresh

Call `sync_results_auto_refresh()` when results toggles change. JS rerun only runs when `results_section` and `results_auto_refresh_schedule` are on.

## Human docs

Mirror registry for non-agents: [`docs/features/ui-debug.md`](../../docs/features/ui-debug.md).
