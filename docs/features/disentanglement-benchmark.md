# Disentanglement benchmark (paper metric)

**Flow →** [`docs/UQLAB_FLOW.md`](../UQLAB_FLOW.md)

Upstream package: [ivopascal/disentanglement_error](https://github.com/ivopascal/disentanglement_error) — vendored under `src/uqlab/vendor/disentanglement_error/` (see `UPSTREAM.md`).

## User API (matches upstream README)

```python
from uqlab.evaluation.benchmarks.disentangling import (
    FastPilotDisentanglingModel,
    calculate_disentanglement_error,
    collect_cifar10_arrays,
    json_results_to_df,
)

X, y = collect_cifar10_arrays()
model = FastPilotDisentanglingModel.from_workflow_defaults()
score = calculate_disentanglement_error(X, y, model, return_json=False)
```

CLI entrypoint (~15 lines): `scripts/runners/run_disentanglement_benchmark.py` (local `pipeline.run`, no API).

## Architecture (Option A)

| Layer | Role |
|-------|------|
| `uqlab_orchestrator.disentanglement_launcher` | **Primary launch** — workflow → vendored `Config` grids → per-point `build_run_yaml` + API create/start |
| `uqlab_orchestrator.campaign_paper_score` | API bridge — aggregate `ExperimentResults` from `results.pt` (global mean aleatoric/epistemic via `uncertainty_pairs`) |
| `uqlab.vendor.disentanglement_error` | Paper metric loops (`label_noise`, `decreasing_dataset`) + `calculate_disentanglement_error` |
| `uqlab.evaluation.benchmarks.disentangling.FastPilotDisentanglingModel` | **Vendor-port adapter** (job runner, not Keras): `fit` → `pipeline.run`, `predict_disentangling` → `results.pt` (Paper mode default) |
| `uqlab.runner.pipeline` | Unchanged single-run engine (API + CLI) |

Default uncertainty pairing in `FastPilotDisentanglingModel` (`predict_mode="paper"`):

- aleatoric ← `expected_entropy` (E[H[p(y|x,θ)]])
- epistemic ← `mutual_info` (H[mean] − E[H])

**Signal preset · DualXDA** (`predict_mode="signal"`): `inverse_coherence_dualxda` + `inverse_mass_dualxda` (legacy alias: `inverse_coherence` + `inverse_mass`).

**Signal preset · EK-FAC** (`predict_mode="signal_ek_fak"`): `inverse_coherence_ek_fak` + `inverse_mass_ek_fak`.

**Swappable:** pass `aleatoric_signal` / `epistemic_signal` explicitly (any keys in `signal_table`) — they override `predict_mode`. Workflow keys `uncertainty_config.aleatoric_signal` / `epistemic_signal` apply when kwargs are omitted.

MC paper metrics require `dropout > 0` and sufficient `mc_passes`; they are pruned from `signal_table` when dropout is zero.

**`predict_disentangling` does not run MC or attribution** — it reads `signal_table` from `results.pt`. Paper bridge columns require MC during the job; DualXDA / EK-FAC bridge columns require the matching backend during the job. See [`shared/config/signals.py`](../../src/uqlab/shared/config/signals.py) (`PREDICT_DISENTANGLING_NOTE`, `bridge_job_requirements`).

Sweep kwargs passed from vendored loops (CLI) or launcher grids (Streamlit):

- `label_noise=` (0–1 fraction) → `aleatoric_noise_percentage` in run YAML
- `dataset_size=` (0–1 fraction) → `under_train_per_class` scaled from `regular_train_per_class`

### Streamlit launch

Step 5 / sidebar **Run benchmark** calls `launch_benchmark_primary` / `launch_benchmark_both` from `uqlab_orchestrator.disentanglement_launcher`. Legacy `launch_paper_profile` in `experiment_launcher.py` delegates to the same module.

Each sweep point is a normal API experiment with `data/experiments/<id>/results/results.pt` — campaign grouping and sweep plots are unchanged.

## Paper plots vs uqlab sweep plots

Both views read the same on-disk campaign runs, but aggregate uncertainty differently.

| Aspect | Paper (`disentanglement_error` / primary UI plot) | uqlab sweep line plot (secondary expander) |
|--------|---------------------------------------------------|--------------------------------------------|
| **Data source** | `ExperimentResults`: `scores`, `aleatorics`, `epistemics` per sweep point | Per-run `results.pt` pool means via `build_sweep_metrics_frame` |
| **X axis** | `Percentage` 0–1 (`label_noises` fraction or `dataset_sizes` fraction) | `noise_percent` 0–100 or `under_train_per_class` (absolute counts) |
| **Y curves** | Three lines on one axis: accuracy + global aleatoric + global epistemic | Left: **one** signal's mean in **one** eval pool; right: accuracy; optional dashed mirror pool |
| **Uncertainty semantics** | Global mean over **all** eval samples from `predict_disentangling` (`{signal}_mean`) | Pool-filtered means (`{signal}_mean_aleatoric` / `{signal}_mean_epistemic`) |
| **Signal pairing** | Paper default: `expected_entropy` + `mutual_info`; swappable via bridge kwargs or `predict_mode="signal"` | User-selectable signal; primary pool follows sweep axis (aleatoric pack for noise, epistemic for under-train) |
| **Correlation** | Label-noise arm → ρ(aleatorics, scores); decreasing-dataset arm → ρ(epistemics, scores) | Not shown (AUROC / UDE live elsewhere) |
| **Implementation** | `campaign_score.py` → `paper_benchmark_plot.py` → `paper_benchmark_plot_viz.py` | `sweep_line_plot.py` → `sweep_line_plot_viz.py` |

### Mapping for paper-primary viz

| Paper field | uqlab campaign equivalent | Aligns today? |
|-------------|---------------------------|---------------|
| `scores[i]` | `accuracy` from `results.pt` | Yes |
| `aleatorics[i]` | mean of `expected_entropy` over all eval samples (paper default) | Yes when `results.pt` present and MC signals computed |
| `epistemics[i]` | mean of `mutual_info` over all eval samples (paper default) | Yes when `results.pt` present and MC signals computed |
| `Percentage` (label noise) | `noise_percent / 100` | Yes (scale conversion) |
| `Percentage` (dataset size) | `under_train_per_class / regular_train_per_class` | Yes (needs config) |
| Pool-filtered diagnostic | `{signal}_mean_aleatoric` / `_mean_epistemic` | **Different** — kept as secondary plot only |

## Legacy / archived

| Item | Location |
|------|----------|
| `run_validation_experiments.py` | `dead_code/scripts/` (UI imports via `validation_runner.py`) |
| Facade coordinators + `BackendExperimentFacade` | `dead_code/facade/` |
| CLI-only `run_disentanglement_benchmark` wrapper | `uqlab.evaluation.benchmarks.disentangling.disentanglement_launcher` |

## Tests

- `tests/test_disentanglement_launcher.py` — workflow → Config grid; mock API launch
- `tests/test_campaign_paper_score.py` — aggregate mock `results.pt` → paper point
- `tests/test_disentangling_model.py` — mocked `pipeline.run`, `predict_disentangling` shapes, `json_results_to_df`
- `tests/test_paper_benchmark_plot.py` — campaign → paper series, plot payload, correlations
- `tests/test_dead_code_imports.py` — smoke imports after archive moves
