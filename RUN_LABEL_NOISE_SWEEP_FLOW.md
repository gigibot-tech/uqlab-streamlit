# Run Label Noise Sweep Flow

This document describes the exact functional flow for a **label noise sweep** in `walaris-cen`, from UI configuration through backend orchestration into `run_fast_uncertainty_classification.py`.

## Scope

This flow covers the case where the user wants to sweep **aleatoric label noise** using the **custom random flipping** path, not the fixed CIFAR-10N built-in noise.

---

## 0. Request path from FastAPI root to the concrete route handlers

Before the label-noise sweep logic starts, FastAPI wires all of these endpoints from the application root.

### Root application wiring

The backend app is created in:

- `walaris-cen/backend/app/main.py`

At startup:

- `lifespan(app)` validates that `run_fast_uncertainty_classification.py` exists under `settings.DTAG_ROOT`
- the database is initialized with `init_db(session)`
- then the FastAPI app includes the API router with:

```python
app.include_router(api_router, prefix=settings.API_V1_STR)
```

So every API route is mounted under:

- `settings.API_V1_STR`
- in practice this is the `/api/v1` prefix seen in your logs

### API router wiring

The shared API router is defined in:

- `walaris-cen/backend/app/api/main.py`

It includes these relevant route groups:

```python
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(batch_experiments.router, prefix="/batch-experiments", tags=["batch-experiments"])
api_router.include_router(uq_benchmarks.router, prefix="/uq-benchmarks", tags=["uq-benchmarks"])
```

That means the requests in your logs resolve like this:

```text
FastAPI app
└── prefix: /api/v1
    ├── /datasets
    │   └── datasets.router
    │       ├── GET /cifar10n/stats
    │       └── GET /cifar10n/confusion-matrix
    │
    ├── /experiments
    │   └── experiments.router
    │       └── GET /no-auth
    │
    ├── /batch-experiments
    │   └── batch_experiments.router
    │       ├── GET /
    │       ├── POST /
    │       ├── GET /{batch_id}
    │       ├── POST /{batch_id}/start
    │       └── GET /{batch_id}/results
    │
    └── /uq-benchmarks
        └── uq_benchmarks.router
            ├── GET /methods
            ├── GET /sweeps
            ├── GET /sweeps/{sweep_id}
            ├── POST /single
            ├── POST /label-noise-sweep
            ├── POST /run
            └── POST /sweep
```

### Mapping your startup/request logs to handlers

Your log lines correspond to these handlers:

- `GET /api/v1/datasets/cifar10n/stats?noise_type=worse_label`
  - handled by `datasets.get_dataset_stats(...)`
  - this lazily imports `CIFAR10NDataset`
  - loads CIFAR-10N with the requested `noise_type`
  - computes total/noisy/clean counts and per-class stats

- `GET /api/v1/experiments/no-auth`
  - handled by the experiments router
  - this is part of the experiment listing / local-dev access path

- `GET /api/v1/batch-experiments`
  - handled by `batch_experiments.list_batch_experiments(...)`
  - queries `BatchExperiment` rows for the local test user

- `GET /api/v1/uq-benchmarks/sweeps`
  - handled by `uq_benchmarks.list_sweeps(...)`
  - queries `BenchmarkSweep` rows and counts associated `BenchmarkResult` rows

- `GET /api/v1/uq-benchmarks/methods`
  - handled by `uq_benchmarks.list_available_methods(...)`
  - first calls `_check_uq_benchmarks_available()`
  - returns `503 Service Unavailable` if the `uq_benchmarks` package or required dependencies are unavailable

### Why these routes appear during startup/UI load

These requests are not the batch execution itself.

They are mostly frontend bootstrap/data-fetch requests used to populate the UI:

- dataset stats panel
- experiment list
- batch experiment list
- benchmark sweep list
- available benchmark methods

So the typical sequence is:

```text
Browser/UI loads
→ frontend calls /api/v1/datasets/cifar10n/stats
→ frontend calls /api/v1/experiments/no-auth
→ frontend calls /api/v1/batch-experiments
→ frontend calls /api/v1/uq-benchmarks/sweeps
→ frontend calls /api/v1/uq-benchmarks/methods
→ user later submits a batch experiment
→ POST /api/v1/batch-experiments
→ batch service expands runs
→ direct executor calls run_fast_uncertainty_classification.py
```

---

## 1. User selects label-noise sweep in the UI

There are two main UI paths that can produce this behavior:

- the **Unified Builder**
- the older **batch experiment / sweep UI**

### Unified Builder path

Entry point:
- `walaris-cen/ui_components/unified_builder.py`

The unified builder renders:
- epistemic controls
- aleatoric controls
- model/training controls
- evaluation controls

Relevant function:
- `render_unified_builder(...)`

Inside it:
- `render_aleatoric_with_sweep(...)` collects aleatoric sweep intent
- `render_model_config()` collects architecture/model settings
- `render_training_config()` collects training settings
- `render_evaluation_config()` collects evaluation settings

When the form is submitted:
- `build_unified_config(...)` assembles the full config
- `handle_unified_builder_submission(...)` sends the experiment(s) to the backend

### Single/batch UI path

Relevant file:
- `walaris-cen/ui_components/experiment_config.py`

The aleatoric section is rendered by:
- `render_aleatoric_config(...)`

This function exposes three label-noise strategies:

1. `No noise (0%, clean labels)`
2. `CIFAR-10N pre-existing noise (~18-40%, not sweepable)`
3. `Custom random flipping (0-100%, sweepable)`

Important behavior:
- only **custom random flipping** is intended for a true label-noise sweep
- this produces a numeric `custom_noise_rate`
- that value is later mapped to backend field:
  - `aleatoric_noise_percentage`

---

## 2. Sweep definition is created in the backend request

For batch sweeps, the backend entry point is:

- `walaris-cen/backend/app/api/routes/batch_experiments.py`

Relevant request model:
- `BatchExperimentCreate`

Important fields:
- `base_config`
- `sweep_definitions`
- `auto_start`

For a label-noise sweep, the sweep definition should target:

- `parameter = "aleatoric_noise_percentage"`

The sweep range is defined by:
- `start`
- `end`
- `step`

Example conceptual payload:

```json
{
  "name": "label_noise_sweep",
  "base_config": {
    "...": "base experiment settings",
    "aleatoric_noise_percentage": 0.0
  },
  "sweep_definitions": [
    {
      "parameter": "aleatoric_noise_percentage",
      "value_type": "float",
      "range": {
        "start": 0,
        "end": 50,
        "step": 10
      }
    }
  ],
  "auto_start": true
}
```

Backend creation flow:
1. `create_batch_experiment(...)`
2. `get_batch_service()`
3. `BatchExperimentService.create_batch(...)`
4. if `auto_start=True`, then `BatchExperimentService.start_batch(...)`

---

## 3. Backend expands the sweep into multiple runs

The batch service creates one run per sweep value.

Conceptually, if the sweep is:

- start = 0
- end = 50
- step = 10

then the generated runs are approximately:

- run 1 → `aleatoric_noise_percentage = 0`
- run 2 → `aleatoric_noise_percentage = 10`
- run 3 → `aleatoric_noise_percentage = 20`
- run 4 → `aleatoric_noise_percentage = 30`
- run 5 → `aleatoric_noise_percentage = 40`
- run 6 → `aleatoric_noise_percentage = 50`

Each run inherits the same base config except for the swept parameter.

---

## 4. Each run is executed through the batch service and direct executor

This is the exact backend execution chain that turns one batch sweep definition into repeated calls to `run_fast_uncertainty_classification.py`.

### Flow diagram

```text
POST /batch-experiments
    │
    ▼
create_batch_experiment(...)                           [backend/app/api/routes/batch_experiments.py]
    │
    ├─ parses request:
    │    - name
    │    - base_config
    │    - sweep_definitions
    │    - auto_start
    │
    ├─ get_batch_service()
    │    │
    │    ▼
    │   BatchExperimentService(DirectExecutor(...))
    │
    ▼
BatchExperimentService.create_batch(...)
    │
    ├─ _generate_values(sweep_definition)
    ├─ _validate_sweep_parameters(...)
    ├─ create BatchExperiment row
    ├─ create one BatchExperimentRun row per sweep value
    ├─ _initialize_storage(batch_id)
    └─ _write_batch_metadata(batch_id)
    │
    └─ if auto_start=True
         │
         ▼
       BatchExperimentService.start_batch(batch_id)
         │
         ▼
       asyncio.create_task(self._run_batch(batch_id))
         │
         ▼
       BatchExperimentService._run_batch(batch_id)
         │
         ├─ load all run IDs for the batch
         ├─ mark batch RUNNING
         ├─ iterate sequentially over runs
         │
         └─ for each run:
              │
              ▼
            _run_single_batch_experiment(batch_id, run_id, position, total_runs)
              │
              ├─ create UncertaintyExperiment row
              ├─ attach experiment_id to BatchExperimentRun
              ├─ parse run.resolved_config_yaml into TrainingConfig
              ├─ _prepare_run_paths(...)
              │    ├─ create run directory
              │    └─ write config.yaml via TrainingConfig.to_yaml_dict()
              │
              └─ await self.executor.execute(config_path, output_dir, progress_callback)
                       │
                       ▼
                     DirectExecutor.execute(...)      [backend/app/services/executors/direct_executor.py]
                       │
                       ├─ emits initializing progress
                       ├─ asyncio.to_thread(self._run_training_sync, ...)
                       │
                       ▼
                     DirectExecutor._run_training_sync(...)
                       │
                       ├─ import run_fast_uncertainty_classification
                       ├─ importlib.reload(...)
                       ├─ from run_fast_uncertainty_classification import main
                       ├─ set_progress_callback(progress_callback)
                       ├─ set sys.argv:
                       │    [script_path, "--config", config_path, "--output_dir", output_dir]
                       └─ call main()
                                │
                                ▼
                              scripts/run_fast_uncertainty_classification.py::main()
                                │
                                ├─ reads generated YAML config
                                ├─ trains/evaluates one run
                                ├─ writes summary.json into output_dir
                                │
                                ▼
                     DirectExecutor._read_results(output_dir)
                       │
                       └─ returns TrainingResult to BatchExperimentService
                                │
                                ▼
                     save_run_results(...)
                       │
                       ├─ mark run COMPLETED
                       ├─ persist AUROC / eval sizes / summary payload
                       └─ _aggregate_batch_results(batch_id)
```

### Important implementation details

The batch route does **not** directly shell out to the script.

Instead, the route creates or retrieves a `BatchExperimentService`, and that service owns a `DirectExecutor`.

Inside the service:

- `create_batch(...)` expands the sweep into concrete child runs
- `start_batch(...)` schedules asynchronous execution
- `_run_batch(...)` executes runs **sequentially**
- `_run_single_batch_experiment(...)` prepares one run’s config and output directory
- `self.executor.execute(...)` is the exact point where the ML script is invoked

### Where `run_fast_uncertainty_classification.py` is actually called

The actual invocation happens in:

- `walaris-cen/backend/app/services/executors/direct_executor.py`

Specifically:

```python
import run_fast_uncertainty_classification
importlib.reload(run_fast_uncertainty_classification)
from run_fast_uncertainty_classification import main

sys.argv = [
    str(self.script_path),
    "--config", str(config_path),
    "--output_dir", str(output_dir)
]

main()
```

So the script is run **in-process by direct Python import**, not by spawning a separate CLI subprocess.

### What gets passed into each run

For every generated sweep point, `_prepare_run_paths(...)` writes:

- `config.yaml`

That YAML is produced from:

- `TrainingConfig.to_yaml_dict()`

So each run gets its own concrete config file containing the swept value, for example:

- `data.aleatoric_noise_percentage = 0`
- `data.aleatoric_noise_percentage = 10`
- `data.aleatoric_noise_percentage = 20`
- etc.

### Output contract between batch backend and ML script

The direct executor expects the ML script to write:

- `summary.json`

into the run output directory.

Then:

- `DirectExecutor._read_results(output_dir)`

loads `summary.json`, extracts AUROC metrics and per-signal results, and returns a `TrainingResult`.

That `TrainingResult` is then persisted back into:

- `BatchExperimentRun`
- `UncertaintyExperiment`
- aggregated batch summary artifacts

---

## 5. The YAML config is loaded by `run_fast_uncertainty_classification.py`

Entry point:
- `walaris-cen/scripts/run_fast_uncertainty_classification.py`

Main function:
- `main()`

The script:
1. parses CLI args
2. loads YAML config
3. converts YAML into `ExperimentConfig`
4. extracts data/model/training/evaluation/path parameters

Relevant config extraction:

- `data.noise_type`
- `data.under_supported_classes`
- `data.under_train_per_class`
- `data.regular_train_per_class`
- `data.eval_per_group`
- `data.aleatoric_noise_percentage`

Specifically:

```python
aleatoric_noise_percentage = data_config.aleatoric_noise_percentage
```

This is the exact field that drives the label-noise sweep behavior.

---

## 6. Dataset loading branches on `aleatoric_noise_percentage`

This is the key decision point in the script.

Relevant logic in:
- `scripts/run_fast_uncertainty_classification.py`

### Branch A: custom label noise sweep path

If:

```python
aleatoric_noise_percentage > 0
```

then the script does **custom noise injection**.

Flow:
1. load `CIFAR10NDataset`
2. force it back to a clean state
3. inject custom random label noise

Exact behavior:

```python
dataset = CIFAR10NDataset(...)
dataset.noisy_labels = None
dataset.noise_mask = None
dataset.noise_rate = 0.0
dataset.inject_custom_noise(noise_percentage=aleatoric_noise_percentage, seed=42)
```

Meaning:
- the script does **not** use the pre-existing CIFAR-10N noisy labels in this branch
- it starts from clean labels
- it injects a fresh random flip rate equal to the current sweep value

### Branch B: fixed CIFAR-10N noise path

If:

```python
aleatoric_noise_percentage == 0
```

then the script loads CIFAR-10N using the configured `noise_type` and expects existing noisy labels.

Flow:
1. load `CIFAR10NDataset(...)`
2. keep the dataset’s built-in noisy labels
3. fail if no noisy labels are available

This is **not** the sweepable custom-noise path.

---

## 7. Split sampling creates train/eval groups

After dataset loading, the script validates the config and creates splits using:

- `sample_indices_for_fast_pilot(...)`

Inputs include:
- `under_supported_classes`
- `under_train_per_class`
- `regular_train_per_class`
- `eval_per_group`
- `aleatoric_noise_percentage`

This produces `split_spec`, which contains:
- `train_indices`
- `clean_eval_indices`
- `aleatoric_eval_indices`
- `epistemic_eval_indices`

Interpretation:
- **clean** = clean, well-supported samples
- **aleatoric** = noisy-label samples
- **epistemic** = under-supported-class samples

For a label-noise sweep, the main thing changing across runs is:
- how many noisy samples exist
- how strong the aleatoric group signal becomes

---

## 8. Model/data mode is prepared

The script determines whether it is running:

- `feature_space`
or
- `end_to_end`

via:

- `get_data_loading_mode(config)`

Then it prepares either:
- DINOv2 embeddings
or
- raw image datasets

This part is architecture-dependent, but the label-noise sweep logic is already fixed earlier by the dataset branch.

So the sweep affects:
- the labels and noise mask in the dataset
- not the architecture-selection logic itself

---

## 9. Model is trained for that sweep value

The script builds the model with:

- `build_model(...)`

Then trains it using either:
- `train_feature_model(...)`
or
- `train_image_model(...)`

This happens independently for each sweep value.

So if the sweep has 6 values, the full training/evaluation pipeline runs 6 separate times.

---

## 10. Uncertainty signals are computed

After training, the script computes:

- MC Dropout uncertainty
- attribution-based signals via DualXDA
- logit-based comparison signals

Examples:
- `msp_uncertainty`
- `predictive_entropy`
- `mutual_info`
- `inverse_coherence`
- `dominance`
- `inverse_mass`
- `inverse_logit_magnitude`

These are then evaluated against:
- aleatoric-vs-rest
- epistemic-vs-rest

---

## 11. What data the evaluation is actually based on

This is the most important section if you want to debug the plots.

After training, `run_fast_uncertainty_classification.py` builds one combined evaluation table from the three eval groups:

- `clean_eval_pack`
- `aleatoric_eval_pack`
- `epistemic_eval_pack`

These are concatenated into:

- `eval_inputs`
- `eval_group_labels`
- `eval_clean_labels`
- `eval_is_noisy`

### Ground-truth evaluation labels

The script defines the evaluation target groups like this:

- clean samples → `GROUP_CLEAN`
- aleatoric samples → `GROUP_ALEATORIC`
- epistemic samples → `GROUP_EPISTEMIC`

Then it builds:

- `aleatoric_positive = eval_group_labels == GROUP_ALEATORIC`
- `epistemic_positive = eval_group_labels == GROUP_EPISTEMIC`

That means every AUROC is computed against the sampled eval groups, not against the training set.

### Exact meaning of the three eval groups

These groups come from `sample_indices_for_fast_pilot(...)` in `uq_classification/data_loader.py`.

They are defined as:

- **clean eval**
  - non-under-supported classes
  - clean labels
  - not used for training

- **aleatoric eval**
  - non-under-supported classes
  - noisy labels
  - not used for training

- **epistemic eval**
  - under-supported classes
  - clean labels
  - not used for training

So the evaluation is based on sampled held-out subsets of the dataset, partitioned into those three uncertainty groups.

### Important debugging implication

If a plot looks strange, the first thing to check is not the frontend.

The first thing to check is whether the run actually had enough samples in:

- `clean_eval_indices`
- `aleatoric_eval_indices`
- `epistemic_eval_indices`

because those exact sampled indices determine all downstream metrics.

---

## 12. How the script computes the plotted metrics

After the eval groups are combined, the script computes a `signal_table`.

Signals include:

- `msp_uncertainty`
- `predictive_entropy`
- `mutual_info`
- `inverse_coherence`
- `dominance`
- `inverse_mass`
- `inverse_logit_magnitude`

### One-vs-rest AUROC

For each signal, the script computes:

- aleatoric-like AUROC
- epistemic-like AUROC

using:

- `binary_auroc(values, aleatoric_positive)`
- `binary_auroc(values, epistemic_positive)`

So each AUROC point is based on:

- one signal column from `signal_table`
- one binary target mask derived from `eval_group_labels`

### 3-way classification metric

The script also computes `macro_f1` using:

- `evaluate_three_way_classification(...)`

That function:

1. builds signal matrices from the signal table
2. splits the eval rows into train/test subsets with balanced group labels
3. trains a tiny linear classifier on the signal values
4. predicts:
   - clean
   - aleatoric
   - epistemic
5. computes macro-F1 on the held-out eval subset

So the 3-way classifier is not trained on raw images or embeddings directly.

It is trained on the uncertainty signal values computed for the eval rows.

---

## 13. The two best files to debug after a run

If you want to understand what the plots are based on, inspect these files first.

### `summary.json`

This is the run-level summary used by the backend.

It contains:

- config used
- train size
- eval sizes
- `one_vs_rest_auroc`
- `macro_f1`

This tells you:

- how many eval samples were actually used
- which AUROC values were produced for each signal
- which macro-F1 values were produced for each signal set

### `per_sample_signals.csv`

This is the best artifact for debugging the evaluation data itself.

It contains one row per evaluated sample with:

- `group`
- `clean_label`
- `is_noisy`
- all signal columns

This file tells you exactly:

- which rows were treated as clean / aleatoric / epistemic
- whether a row was actually noisy
- what signal values were assigned to that row

If you want to understand “what data was this plot based on?”, this is the first file to inspect.

---

## 14. How batch plots are built

The batch backend does not recompute uncertainty metrics.

Instead, it aggregates per-run summaries that were already computed by `run_fast_uncertainty_classification.py`.

Batch results are exposed through:

- `GET /batch-experiments/{batch_id}/results`

Entry point:
- `get_batch_results(...)` in `backend/app/api/routes/batch_experiments.py`

The backend returns aggregated series built from stored run results.

So batch plots are based on:

- x-axis = swept parameter value
- y-axis = per-run AUROC already saved in `summary.json`

That means the provenance chain is:

```text
sampled eval indices
→ eval packs
→ eval_group_labels + signal_table
→ AUROC / macro-F1 in summary.json
→ backend aggregation
→ frontend plot
```

---

## 15. Practical debugging workflow

If you want to debug one suspicious plot yourself, use this order:

1. identify the exact run directory
2. open `summary.json`
3. check:
   - `eval_sizes`
   - `one_vs_rest_auroc`
   - `macro_f1`
4. open `per_sample_signals.csv`
5. verify:
   - `group`
   - `is_noisy`
   - signal columns
6. compare the CSV rows to the AUROC values in `summary.json`
7. only after that inspect batch or grid plots in the UI

### Short rule

Do **not** start from Streamlit if you want truth.

Start from:

- `per_sample_signals.csv`
- `summary.json`

because those are the direct outputs of the evaluation pipeline.

---

# Exact functional summary

## Definition of “run label noise sweep”

In this codebase, a **label noise sweep** means:

> create multiple experiment runs where `data.aleatoric_noise_percentage` changes across runs, and for each run `run_fast_uncertainty_classification.py` reloads the dataset, injects that percentage of custom random label flips, trains a model, evaluates uncertainty signals, and saves results.

---

# Minimal end-to-end flow

```text
UI selects "Custom random flipping"
→ user enables sweep over noise percentage
→ backend receives sweep on aleatoric_noise_percentage
→ batch service expands sweep into multiple runs
→ each run launches run_fast_uncertainty_classification.py with its own YAML
→ script reads data.aleatoric_noise_percentage
→ if > 0: reset dataset to clean and inject custom noise
→ sample train/eval splits
→ train model
→ compute uncertainty signals
→ save per-run results
→ backend aggregates sweep results
```

---

# Important caveat

A sweep over label noise should use:

- `Custom random flipping (0-100%, sweepable)`

and **not**:

- `CIFAR-10N pre-existing noise (~18-40%, not sweepable)`

because CIFAR-10N noise is fixed by `noise_type`, while the sweepable path is driven by:

- `data.aleatoric_noise_percentage`

---

# Most important variable

If you want the single exact variable that defines the label-noise sweep, it is:

- `data.aleatoric_noise_percentage`

That is the parameter that changes from run to run and causes the script to inject different amounts of random label noise.