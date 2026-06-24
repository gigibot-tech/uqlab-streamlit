# Execution Flow & Configuration Guide

**Date**: 2026-06-24 (updated)  
**Purpose**: Accurate map of datamodels, config transformation, and execution paths.

---

## Executive summary

| Concept | Location | Role |
|---------|----------|------|
| **UI state** | `session_state.workflow` | Dict from Streamlit forms (not executed directly) |
| **Run YAML** | Built by `run_spec.build_run_yaml` | Dict matching `ExperimentConfig` schema |
| **Entry config** | `ExperimentConfig` | Single dataclass loaded by the pipeline |
| **Launch** | `experiment_launcher` | POST configs to backend API |
| **Execution** | `DirectExecutor` → `pipeline.run` | In-process ML (executor wraps runner) |

**One datamodel at execution time:** [`ExperimentConfig`](src/uqlab/shared/config/classification.py)  
**One on-disk format:** YAML (`config.yaml` per experiment)  
**One execution API:** `uqlab.runner.pipeline.run(config_path, output_dir)`

---

## Q1: Does the frontend create ExperimentConfig and use DirectExecutor?

**Partially.** The UI never holds an `ExperimentConfig` object directly. Flow:

```
1. UI (ui_components)
   session_state.workflow  — dict from Step 1–4 forms

2. Bridge (uqlab_orchestrator)
   run_spec.build_run_yaml(workflow)  → YAML-shaped dict
   generate_sweep_runs(workflow)      → list of (sweep_kind, workflow_variant)
   experiment_launcher.launch_workflow_experiments  → HTTP POST to backend

3. Backend (FastAPI)
   Writes config.yaml under data/experiments/<id>/
   DirectExecutor.execute(config_path, output_dir)

4. DirectExecutor (in-process, thread pool)
   from uqlab.runner.pipeline import run
   pipeline.run(config_path, output_dir)

5. Pipeline (uqlab.runner)
   ExperimentConfig.from_yaml(config_path)
   validate → run_experiment_core(config, results_dir)

6. Core (uqlab.runner.fast_pilot_core)
   train → evaluate signals → write artifacts
```

### DirectExecutor vs runner — not duplicates

| Layer | Package | What it does |
|-------|---------|--------------|
| **DirectExecutor** | `backend/` | Backend infra: thread pool, progress callbacks, DB updates; **calls** `pipeline.run` |
| **pipeline.run** | `uqlab/runner/` | ML job: load YAML → validate → `run_experiment_core` |
| **run_experiment_core** | `uqlab/runner/` | Actual training + evaluation |

The executor does **not** replace the runner. It is a thin wrapper so the FastAPI process can invoke the ML stack in-process (no subprocess). `SubprocessExecutor` was removed (2026-06-24); only `DirectExecutor` remains.

CLI dev path (no backend): `scripts/runners/run_fast_uncertainty_classification.py` → `pipeline.run` directly.

---

## Q2: Single entry datamodel?

**Yes — `ExperimentConfig`.**

```python
# src/uqlab/shared/config/classification.py
@dataclass
class ExperimentConfig:
    data: DataConfig
    model: ModelConfig
    training: TrainingConfig
    evaluation: EvalConfig
    paths: PathsConfig
    seed: int = 42
    device: str = "auto"

    @classmethod
    def from_yaml(cls, path: Path) -> ExperimentConfig: ...
```

Loaded only inside `pipeline.run` (or `run_config` for tests). There is no `to_yaml` on the dataclass — YAML is produced as a dict by `run_spec` and written to disk by the backend.

---

## Q3: Does run_spec build YAML?

**Yes.**

| Function | File | Input → Output |
|----------|------|----------------|
| `build_run_yaml(workflow)` | [`run_spec.py`](src/uqlab_orchestrator/run_spec.py) | workflow dict → one YAML-shaped dict |
| `generate_sweep_runs(workflow)` | [`run_spec.py`](src/uqlab_orchestrator/run_spec.py) | workflow dict → list of `(sweep_kind, workflow_variant)` for per-class, four-region, legacy, and sweep modes |

```
workflow dict  →  build_run_yaml()  →  { data, model, training, evaluation, paths }
                                      →  written to config.yaml
                                      →  ExperimentConfig.from_yaml()
```

---

## Q4: Does experiment_launcher use the runner/pipeline?

**No.** It submits to the backend API only.

```python
# experiment_launcher.launch_workflow_experiments (simplified)
runs = generate_sweep_runs(workflow)
for sweep_kind, wf in runs:
    yaml_dict = build_run_yaml(wf)
    requests.post(f"{API_BASE_URL}/api/v1/experiments/no-auth", json={...})
    requests.post(f".../experiments/no-auth/{exp_id}/start", ...)
```

The backend's `DirectExecutor` is what eventually calls `pipeline.run`.

---

## Q5: What is `disentanglement_launcher`?

**Live primary launch entry** (legacy name from paper-benchmark / vendored `disentanglement_error` code).

```
streamlit_app_progressive.py
    → launch_benchmark_primary()     # disentanglement_launcher.py
        → launch_workflow_experiments()  # experiment_launcher.py
            → generate_sweep_runs()      # run_spec.py
            → build_run_yaml()
            → POST /api/v1/experiments/...
```

It is orchestrator code, not a separate package. The name reflects historical paper sweeps (Fig 3/4), not a dead subsystem.

---

## Package dependencies (intended direction)

```
ui_components/          Streamlit UI (lives under src/uqlab/ui_components/)
    ↓ imports
uqlab_orchestrator/     Config bridge, launch, disk registry
    ↓ imports
uqlab/                  ML core: data, models, runner, evaluation
    ├─ shared/config/   ExperimentConfig schema
    └─ runner/          pipeline.run → run_experiment_core
```

**Wrinkle:** `ui_components` is physically inside the `uqlab` Python package namespace but is logically the UI layer.

**2026-06-24 fixes:**
- Orchestrator → UI inversion removed (`experiment_registry` moved to orchestrator).
- Core → bridge inversion removed (`config_diff` now imports `flatten_dict` / `find_config_differences` from `uqlab.experiment_config_flat`, not `sweep_groups`).

**Remaining deferred imports (documented, acceptable):**
- `four_region_validation.py`, `thesis_diagram.py` — lazy imports of orchestrator config builders inside functions (not import-time).

### Why not fold orchestrator into uqlab?

- `uqlab` should stay importable for notebooks/CLI without Streamlit or HTTP launch logic.
- `uqlab_orchestrator` holds workflow→YAML and API submission without rendering UI.
- Merging would couple ML core to launch/API concerns.

---

## Full execution diagram

```
┌──────────────────────────────────────────────────────────────┐
│ UI — session_state.workflow (dict)                           │
│ step1_dataset … step5_review, launch_panel                   │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ ORCHESTRATOR                                                 │
│ launch_benchmark_primary → launch_workflow_experiments         │
│ run_spec.generate_sweep_runs / build_run_yaml                │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP POST
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ BACKEND — FastAPI                                              │
│ write config.yaml → DirectExecutor.execute (in-process)        │
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ uqlab.runner.pipeline.run                                      │
│ load ExperimentConfig.from_yaml → validate → run_experiment_core│
└────────────────────────────┬─────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────────────────────┐
│ Artifacts: summary.json, results.pt, per_sample_signals.csv    │
│ DB updated → UI reads results                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Related docs

| Doc | Focus |
|-----|-------|
| [`ARCHITECTURE_CLARIFICATION.md`](ARCHITECTURE_CLARIFICATION.md) | Package boundaries |
| [`docs/architecture/evaluation-pipeline.md`](docs/architecture/evaluation-pipeline.md) | Evaluation phases inside `run_experiment_core` |
| [`docs/UQLAB_FLOW.md`](docs/UQLAB_FLOW.md) | System overview + artifact contract |

---

**Status**: Aligned with code as of 2026-06-24.
