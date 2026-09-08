# Checkpoint Arsenal (Step 2.5)

Optional Progressive UI step between **Step 2: Training** and **Step 3: Uncertainty** for reviewing resumable experiment checkpoints before launching new runs.

## Purpose

Help researchers avoid redundant experiments by showing:

- All runs with on-disk `results/checkpoint.pt` (resumable weights)
- Grouping by **model architecture** (ResNet18, DINOv2-small, …)
- **Sweep rows** per model: checkpoints with the same stable training setup; chips differ on sweep axes (label noise %, under-train, MC passes, …)
- **Shared setup** expander once per model section (mode/median baseline across all checkpoints in that model)
- **Chip labels** show sweep values (`50%`, `under=300`) — hover for full tooltip including run name and ID
- **Click** a chip to load config into Step 2 resume mode

This differs from **campaign PDF export**, which covers one smart-group sweep with deltas vs the previous run in sweep order.

## Layout

```
ResNet18 (85 checkpoints) ▼          ← collapsed when >12 checkpoints
  Shared setup (12 params) ▼         ← dataset, epochs, lr, … shown once
  Varies: Label noise (%) · 15 checkpoints
    [0%] [10%] [25%] …
  Varies: Under-train / class · 10 checkpoints
    [u50] [u100] …
```

**Filters:** model, sweep axis, text search (id/name/sweep value), hide singletons.

## Scope (v1)

- API experiments that have `data/experiments/<id>/results/checkpoint.pt`
- Client-side grouping (no dedicated REST endpoint)
- Session cache in `st.session_state["checkpoint_arsenal_cache"]`

Disk-only orphans (deleted from DB) are out of scope for v1.

## UI entry points

1. **Step 2.5** in the main workflow (optional; does not block Step 3)
2. **Step 2** → “Browse all checkpoints…” when using existing checkpoint
3. **Sidebar** experiment selector → “Checkpoint arsenal” button

Toggle visibility: debug panel → `Step 2.5 · Checkpoint arsenal`.

Inline and dialog use the **same renderer** (no duplicate HTML preview).

## Backend for stable checkpoints

Use production mode so training is not killed by auto-reload:

```bash
cd backend
./start_backend_prod.sh
```

See [BACKEND_MODES.md](../../backend/BACKEND_MODES.md). Step 5 review also reminds you to use prod mode for sweeps.

## Modules

| Module | Role |
|--------|------|
| `evaluation/pipeline/config_diff.py` | Shared config flattening, `chip_display_label`, cluster fingerprints |
| `evaluation/pipeline/checkpoint_arsenal.py` | Build `CheckpointArsenal`, `filter_arsenal_sections` |
| `ui_components/workflow/step2_5_checkpoint_arsenal.py` | Step 2.5 shell |
| `ui_components/results/checkpoint_arsenal_viz.py` | Dialog + inline renderer, filter bar |
| `ui_components/results/model_group_row.py` | Collapsible model sections, chip buttons |

## Tests

```bash
PYTHONPATH=src PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_checkpoint_arsenal.py -q
```
