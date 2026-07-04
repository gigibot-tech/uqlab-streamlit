# uqlab_core — start here

Minimal uncertainty-quantification pipeline for notebooks and assignments.

## Five calls

```python
from uqlab_core import (
    setup_notebook,
    build_run_data,
    run_paper_experiment,
    run_uncertainty_eval,
    run_four_region_benchmark,
)

ctx = setup_notebook(seed=42)
# … or full paper run via run_four_region_benchmark(RUNS, ctx)
```

| Call | What it does |
|------|----------------|
| `setup_notebook()` | Bootstrap path, seed, device |
| `build_run_data()` | YAML → dataset + tensor packs |
| `run_paper_experiment()` | Train + eval + save artifacts |
| `run_uncertainty_eval()` | Signals + AUROC (after train) |
| `run_four_region_benchmark()` | Assignment notebook runs |

## Layout

```
uqlab_core/
  data/       — build_run_data, four_region splits, datasets
  models/     — training, architectures
  runner/     — execute, notebook_run, train_eval
  evaluation/ — run_uncertainty_eval, signals, metrics
  shared/     — ExperimentConfig, signal config
```

Full lab (Streamlit, campaigns, thesis diagrams) lives in sibling package `uqlab`.
