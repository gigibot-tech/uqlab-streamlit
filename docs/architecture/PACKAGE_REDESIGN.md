# Package redesign — evaluation umbrella + consolidation

**Status:** Phase 0–6 implemented (2026-06). `evaluation/pipeline/` is a compat shim only.

## Target shape

```
src/uqlab/
├── data/                    # datasets, splits, experiment data setup
│   ├── setup.py             # ExperimentConfig → ExperimentDataContext (was pipeline/data_setup)
│   ├── experiment_loader.py  # SplitSpec, index sampling, DINOv2 feature cache
│   ├── class_regions.py     # four-region partition
│   ├── benchmark_axes.py    # which eval pools a config expects
│   └── loaders/             # per-dataset loaders
├── models/                  # architectures, factory, MC dropout
├── runner/
│   ├── execute.py           # run_from_yaml / run_from_python_config
│   ├── experiment_core.py   # train + eval orchestration
│   └── phases/              # runner execution stages
│       ├── config_view.py   # RunConfigView, extract_run_config (was experiment_setup)
│       ├── eval.py          # collect/score uncertainty signals
│       ├── eval_signal_config.py
│       └── recovery.py      # zwischen recovery
└── evaluation/              # umbrella (signals + metrics + reporting + benchmarks)
    ├── signals/             # per-sample signal computation
    │   ├── dualxda_tracer.py   # was legacy/triage/dualxda_axioms
    │   ├── attribution*.py, registry, sources, …
    ├── metrics/             # pure scoring + results.pt contract
    │   ├── scoring.py       # AUROC, 3-way classifier (was metrics.py)
    │   └── artifacts.py     # EvalRunArtifacts
    ├── reporting/           # plot payloads, campaign PDFs, CSV writers
    │   ├── sweep_line_plot.py, campaign_*.py, thesis_diagram.py, …
    │   └── result_writers.py
    ├── benchmarks/          # paper disentangling bridges
    └── pipeline/            # DEPRECATED shim → re-exports new paths
```

## Consolidation decisions (per folder)

### `data/` — merged orchestration, kept primitives separate

| Keep separate | Why |
|---------------|-----|
| `experiment_loader.py` | Low-level split sampling + feature extraction/cache |
| `class_regions.py` | Four-region index logic |
| `benchmark_axes.py` | Config → expected eval pools |
| `classification_dataset.py` + `image_dataset.py` | Protocol/helpers vs image tensor wrapper |
| `loaders/*` | Per-dataset I/O |

| Consolidated | From |
|--------------|------|
| `setup.py` | `evaluation/pipeline/data_setup.py` — single config→context entry; delegates to `experiment_loader` + `class_regions` |

**Not merged:** `experiment_loader` into `setup` — different layers (primitives vs orchestration).

### `evaluation/metrics/` — folder consolidation only

| File | Role |
|------|------|
| `scoring.py` | Pure AUROC / confusion / 3-way classifier math |
| `artifacts.py` | `EvalRunArtifacts` read contract for `results.pt` |

**Not merged:** scoring vs artifacts — compute vs consume are different concerns.

Shims at `evaluation/metrics.py` and `evaluation/artifacts.py` preserve old import paths.

### `evaluation/signals/` — tracer moved in, backends kept separate

| Consolidated | From |
|--------------|------|
| `dualxda_tracer.py` | `legacy/triage/dualxda_axioms.py` |

| Keep separate | Why |
|---------------|-----|
| `attribution.py` vs `attribution_distribution.py` | Structure signals vs full-vector distribution measures |
| `mc_dropout.py`, `ek_fak.py`, `graddot.py` | Distinct attribution backends |
| `registry.py` + `catalog.py` + `sources.py` | Registry pattern (meta / compute / primitives) |

### `evaluation/reporting/` — all post-run figure/PDF/CSV assembly

Moved from `evaluation/pipeline/`: sweep plots, campaign PDF, checkpoint arsenal, thesis diagram, `result_writers.py`.

### `runner/phases/` — execution stages (not evaluation)

Moved from `evaluation/pipeline/`: eval, config_view, eval_signal_config, recovery.

### Notebook helpers — no merge

`notebook_support/` remains a thin shim over `shared/notebook_utils/` (plot selection only; not ML logic).

## Entry surfaces and runner

| Surface | Uses `runner/`? |
|---------|-----------------|
| Streamlit progressive | No — orchestrator → API → backend `DirectExecutor` → `runner.execute` |
| Backend / Flask | Yes — in-process `run_from_yaml` |
| CLI `scripts/runners/*` | Yes |
| Notebooks (load mode) | No — `run_artifacts`, `evaluation.metrics`, signals |
| Notebooks (run mode) | Yes — `run_from_python_config` |

## Notebook NaN fix (Phase 0)

`load_per_sample_table(..., max_rows=500)` truncated clean-first CSVs. Fix: `max_rows=None` for aggregation; stratified sampling in `attribution_rebuild` when capping eval rows.

## Backward compatibility

- `uqlab.evaluation.pipeline.*` — lazy shim in `pipeline/__init__.py`
- `uqlab.evaluation.metrics` / `artifacts` / `result_writers` — one-line re-export shims
- `evaluation.legacy.triage.dualxda_axioms` — shim to `signals.dualxda_tracer`

Prefer new imports in new code:
```python
from uqlab.data.setup import prepare_experiment_data
from uqlab.runner.phases.eval import score_uncertainty_signals
from uqlab.evaluation.reporting.sweep_line_plot import build_sweep_line_plot
from uqlab.evaluation.metrics.scoring import binary_auroc
from uqlab.evaluation.signals.dualxda_tracer import DualXDATracer
```

## Out of scope (future)

- Extract `ui_components/` → top-level `streamlit_ui/`
- Rename `runner/` → `execution/`
- Numbered `1_data`…`7_orchestration` folders (never implemented)
