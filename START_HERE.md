# Start here

Read this page first. You do not need the older `docs/architecture/*` files unless you are debugging history.

## Run the app

```bash
cd uqlab-streamlit
make install          # once
make run-backend      # terminal 1 — API on :8000
make run-frontend     # terminal 2 — progressive UI on :8501
```

Primary UI: [`streamlit_app_progressive.py`](streamlit_app_progressive.py)  
Legacy UI: [`streamlit_app.py`](streamlit_app.py) (deprecated — use progressive)

Local Flask wizard (no API): [`uqlab-flask/app.py`](uqlab-flask/app.py) on :5001

## The four boxes (MLgym map)

| Box | Folder | What it does |
|-----|--------|----------------|
| **Config** | [`src/uqlab_orchestrator/`](src/uqlab_orchestrator/) | `workflow` dict → nested YAML via [`run_spec.py`](src/uqlab_orchestrator/run_spec.py) |
| **ML core** | [`src/uqlab/`](src/uqlab/) | Data, model factory, train, eval |
| **Job** | [`src/uqlab/runner/pipeline.py`](src/uqlab/runner/pipeline.py) | **Single execution entry** — load → validate → execute |
| **UI** | [`src/uqlab/ui_components/`](src/uqlab/ui_components/) | Streamlit widgets only; edits `workflow`, calls orchestrator |

```text
wizard steps 1–5  →  workflow dict
       ↓
run_spec.build_run_yaml()
       ↓
config.yaml on disk
       ↓
pipeline.run(config_path, output_dir)   ← always this
       ↓
results/summary.json + results.pt
```

Wizard → YAML field mapping: [`docs/features/workflow-config.md`](docs/features/workflow-config.md)

## Run one experiment (no UI)

```bash
PYTHONPATH=src python scripts/run_fast_uncertainty_classification.py \
  --config path/to/config.yaml \
  --output_dir data/experiments/<run_id>/results
```

Or from Python:

```python
from pathlib import Path
from uqlab.runner.pipeline import run

run(Path("config.yaml"), Path("output_dir"))
```

Details: [`src/uqlab/runner/README.md`](src/uqlab/runner/README.md)

## Design patterns (already in the code)

No DI framework — reproducibility comes from **one config file + one pipeline**:

- **Pipeline / IoC** — [`runner/patterns.py`](src/uqlab/runner/patterns.py): stages own the flow, callers do not.
- **Factory** — [`models/factory.py`](src/uqlab/models/factory.py): `build_model(config)`.
- **Strategy** — [`shared/config/signals.py`](src/uqlab/shared/config/signals.py): `evaluation.signals` picks predictive / logit / attribution families.

## Clone-friendly core

Copy these for a new project; treat UI and backend as replaceable shell:

```
src/uqlab/                    # ML core
src/uqlab_orchestrator/       # config + launch + sweep grouping
scripts/run_fast_uncertainty_classification.py
```

## Results and plots

- API experiments: **Results** section below Step 5 (toggle in sidebar **UI debug**).
- Hiding UI blocks → sidebar **UI debug**; see [`.cursor/skills/ui-debug/`](.cursor/skills/ui-debug/SKILL.md) and [`docs/features/ui-debug.md`](docs/features/ui-debug.md).
- Paper sweeps = **two separate 1D campaigns** (Fig 3 under-train + Fig 4 label noise), not a 2D grid. Launch from Step 5 or sidebar **Quick launch**.
- 3-line sweep plot: signal pool means + accuracy (not AUROC) — needs `results.pt` on disk.
- Sweep grouping: [`uqlab_orchestrator/sweep_groups.py`](src/uqlab_orchestrator/sweep_groups.py)

## Do not read (unless debugging)

- `docs/architecture/*` — historical rework notes
- `src/uqlab/ui_components/UI_COMPONENTS_*.md` — migration logs
- `archive/` — old experiments
