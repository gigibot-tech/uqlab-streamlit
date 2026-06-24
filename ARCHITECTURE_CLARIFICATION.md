# Architecture Clarification: Package Boundaries & Responsibilities

**Date**: 2026-06-24 (updated after orchestrator/UI inversion fix)  
**Purpose**: Accurate map of package boundaries and how experiments flow from UI to ML core.

---

## Executive Summary

| Layer | Package | Role |
|-------|---------|------|
| Frontend | `uqlab.ui_components` | Streamlit widgets, `session_state.workflow` |
| Bridge | `uqlab_orchestrator` | Workflow → YAML/`ExperimentConfig`, sweep expansion, launch preflight, disk registry |
| Backend | `backend/` | FastAPI, DB, **in-process** training via `DirectExecutor` |
| ML core | `uqlab/` | Data, models, training, evaluation, artifacts |

**Dependency direction (correct):** UI → bridge → core. The bridge must not import the UI package.

**2026-06-24 fix:** `experiment_registry.py` moved from `ui_components/results/` to `uqlab_orchestrator/`; `launch_preflight` no longer imports `campaign_groups` from the UI layer.

---

## Layer diagram

```
┌─────────────────────────────────────────────────────────┐
│  FRONTEND — uqlab.ui_components                         │
│  Streamlit widgets, session_state.workflow              │
└────────────────────┬────────────────────────────────────┘
                     │ imports bridge
                     ▼
┌─────────────────────────────────────────────────────────┐
│  BRIDGE — uqlab_orchestrator                            │
│  run_spec.generate_sweep_runs, experiment_launcher,     │
│  launch_preflight, experiment_registry (disk/config)    │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP POST (experiment_launcher)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  BACKEND — backend/                                     │
│  FastAPI routes, DirectExecutor → pipeline.run          │
└────────────────────┬────────────────────────────────────┘
                     │ in-process (thread pool)
                     ▼
┌─────────────────────────────────────────────────────────┐
│  ML CORE — uqlab/                                       │
│  runner.pipeline.run → fast_pilot_core.run_experiment   │
│  data / models / evaluation                             │
└─────────────────────────────────────────────────────────┘
```

---

## Q1: Is `uqlab_orchestrator` frontend logic?

**No.** It is a **bridge layer** — config transformation and launch orchestration with **no Streamlit imports**.

| Package | Responsibility | Streamlit? |
|---------|----------------|------------|
| `ui_components/` | Render UI, collect input | Yes |
| `uqlab_orchestrator/` | Workflow → configs, sweeps, preflight, disk registry | No |

`ui_components` should **not** live inside `uqlab_orchestrator`. They are separate packages so the bridge can be used from CLI/notebooks without Streamlit.

---

## Q2: Workflow and sweep generation

**Workflow dict** lives in `session_state` (frontend).

**Sweep expansion** happens in the bridge:

- [`run_spec.generate_sweep_runs`](src/uqlab_orchestrator/run_spec.py) reads `workflow["uncertainty_config"]` and produces N YAML-shaped run configs (including per-class and four-region modes).
- [`experiment_launcher.launch_workflow_experiments`](src/uqlab_orchestrator/experiment_launcher.py) calls `generate_sweep_runs`, then POSTs each config to the backend API.

Frontend collects sweep parameters; bridge generates concrete configs. That split is intentional — the UI should not duplicate sweep logic from `run_spec.py`.

---

## Q3: ExperimentConfig and execution path

```
1. UI builds workflow dict (session_state)
2. Bridge: generate_sweep_runs / build_run_yaml → config YAML dict
3. experiment_launcher: POST /api/v1/experiments/no-auth (+ /start)
4. Backend DirectExecutor: uqlab.runner.pipeline.run(config_path, ...)  [in-process]
5. pipeline.run → run_experiment_core → train + evaluate + write artifacts
```

### DirectExecutor (sole implementation)

| Class | Status | Behavior |
|-------|--------|----------|
| [`DirectExecutor`](backend/app/services/executors/direct_executor.py) | **Production** | Calls `uqlab.runner.pipeline.run` **in-process** (thread pool) |

`SubprocessExecutor` was removed (2026-06-24). The `TrainingExecutor` ABC remains as the DI seam for future executors (Docker, Celery, etc.).

**Analogy:**
- `DirectExecutor` = scheduler (invokes the pipeline in the backend process)
- `uqlab.runner` = worker (does ML)

---

## Q4: When do we enter the `uqlab` package?

At **`uqlab.runner.pipeline.run`**, whether called from:

- `DirectExecutor` (backend, in-process), or
- CLI `run_fast_uncertainty_classification.py` (local dev)

Inside `uqlab`:

1. **`pipeline.run`** — load/validate `ExperimentConfig`, call core
2. **`fast_pilot_core.run_experiment_core`** — data setup, train, signal eval, artifacts

See also [`docs/architecture/evaluation-pipeline.md`](docs/architecture/evaluation-pipeline.md) for the evaluation phase breakdown.

---

## Package responsibility matrix

| Package | Responsibility | Depends on | Used by |
|---------|----------------|------------|---------|
| `ui_components/` | UI rendering | Streamlit, bridge | User |
| `uqlab_orchestrator/` | Config bridge, launch, disk registry | `uqlab.shared.config`, `uqlab.data`, `uqlab.evaluation` (light) | UI, backend bootstrap |
| `backend/` | API + in-process execution | bridge, `uqlab.runner` | UI (via HTTP) |
| `uqlab/runner/` | Pipeline orchestration | `uqlab.*` | backend, CLI |
| `uqlab/data/`, `models/`, `evaluation/` | ML core | PyTorch stack | runner |

---

## Prior architectural smell (fixed 2026-06-24)

**Problem:** `uqlab_orchestrator` imported `uqlab.ui_components` in:

- `launch_preflight.py` → `experiment_registry`, `campaign_groups`
- `plot_probe/duplicate_gate.py` → `experiment_registry`

That inverted the dependency graph (bridge → UI).

**Fix:**

1. Moved [`experiment_registry.py`](src/uqlab_orchestrator/experiment_registry.py) into `uqlab_orchestrator/` (pure disk/config logic; uses `uqlab.runtime_paths.experiments_root`).
2. Replaced `launch_preflight`'s lazy `campaign_groups` import with `group_experiments_intelligently` from [`sweep_groups.py`](src/uqlab_orchestrator/sweep_groups.py) for resume-offer grouping.

UI modules now import `uqlab_orchestrator.experiment_registry` — the correct direction.

---

## Naming notes (optional future work)

| Current name | Issue | Note |
|--------------|-------|------|
| `uqlab_orchestrator` | Sounds like it runs experiments | It transforms configs and submits to backend; execution is in `uqlab.runner` |
| `DirectExecutor` | Sounds like synchronous inline call | Accurate today (in-process `pipeline.run`); not a subprocess |

Renames are low priority; documentation accuracy matters more than package renames.

---

## Related documentation

| Doc | Focus |
|-----|-------|
| [`docs/UQLAB_FLOW.md`](docs/UQLAB_FLOW.md) | System overview + artifacts |
| [`docs/architecture/evaluation-pipeline.md`](docs/architecture/evaluation-pipeline.md) | Evaluation pipeline structure |
| [`docs/archive/STEP3_FLOW_ANALYSIS.md`](docs/archive/STEP3_FLOW_ANALYSIS.md) | Historical UI → runner notes |

---

**Status**: Architecture doc aligned with code; orchestrator → UI inversion removed.
