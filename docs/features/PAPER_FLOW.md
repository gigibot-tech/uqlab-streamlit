# Paper API → UQLab mapping

Maps the Keras `InformationTheoreticModel` / `calculate_disentanglement_error` demo to UQLab modules and on-disk artifacts.

**If you only read one function:** [`run_experiment_core`](../../src/uqlab/runner/experiment_core.py) (CLI) or [`run_notebook_experiment`](../../src/uqlab/runner/notebook_run.py) (notebooks).

## Single run (`run_experiment_core` or `run_paper_experiment`)

| Paper (Keras) | UQLab | Module | Artifact |
|---|---|---|---|
| `model.fit(x, y)` | load + train | [`build_run_data`](../../src/uqlab/data/pipeline.py) → [`run_paper_experiment`](../../src/uqlab/runner/train_eval.py) → [`models/training.py`](../../src/uqlab/models/training.py) | `checkpoint.pt`, `training_data.csv` |
| MC → `expected_entropy`, `mutual_information` | MC dropout signals | [`run_uncertainty_eval`](../../src/uqlab/evaluation/pipeline.py) step 1 | `zwischen/01..05_*.pt`, `signal_table` in `results.pt` |
| `predict_disentangling(x)` | per-sample vectors | `run_uncertainty_eval` step 2 | `per_sample_signals.csv`, `results.pt` |
| run record | summary dict | [`evaluation/reporting/run_summary.py`](../../src/uqlab/evaluation/reporting/run_summary.py) | `summary.json`, `summary.md`, `signal_formulas.json` |

### SAVE vs LOG (one run)

| Prefix / helper | stdout | disk |
|---|---|---|
| `print_experiment_configuration`, `log_run_data_context`, `log_run_complete` | yes | no |
| `save_zwischen_result` | no | `zwischen/*.pt` |
| `score_uncertainty_signals` | no | `per_sample_signals.csv` (via `run_uncertainty_eval`) |
| `persist_run_outputs` | no | `summary.json`, `results.pt`, `checkpoint.pt`, … |

## Many runs (campaign — NOT in single run)

| Paper | UQLab | Output |
|---|---|---|
| `calculate_disentanglement_error(...)` | [`campaign_score.py`](../../src/uqlab/evaluation/reporting/campaign_score.py) + vendor | DE scalar, sweep JSON |
| `json_results_to_df(...)` | `PaperSweepSeries.to_dataframe()` | long CSV columns |
| `df.groupby(...).plot()` | [`persist_campaign_paper_plot`](../../src/uqlab/evaluation/reporting/paper_benchmark_plot.py) | **`{sweep_kind}_three_line.png`** + `{sweep_kind}_curves.csv` |

**Campaign end (automatic):** validation runner calls `persist_campaign_paper_plot` after each sweep.

**Manual:** `PYTHONPATH=src python scripts/analysis/disentanglement_error.py curves --campaign-dir … --plot`

## Notebook minimal flow

See [`notebooks/cifar10_paper_flow.ipynb`](../../notebooks/cifar10_paper_flow.ipynb) or the four-region notebook guide [`four-region-notebook.md`](four-region-notebook.md).

```python
from uqlab.data import build_run_data
from uqlab.runner.notebook_run import setup_notebook, run_notebook_experiment

ctx = setup_notebook(seed=42)
bundle = build_run_data(config, ctx.root, seed=ctx.seed, device=ctx.device)
# … or one call:
run_notebook_experiment(config, results_dir, project_root=ctx.root, device=ctx.device)
```

For manual control after data:

```python
from uqlab.runner.train_eval import run_paper_experiment

result = run_paper_experiment(
    config=config,
    run_cfg=run_cfg,
    results_dir=results_dir,
    run_cache_dir=results_dir / "cache",
    data_pack=bundle.data_pack,
    split_spec=bundle.split_spec,
    device=device,
    seed=seed,
    training_config=config.training,
    data_config=config.data,
    model_config=config.model,
    eval_config=config.evaluation,
    ds_spec=run_cfg.dataset_spec,
    persist=True,
    log=True,
)
```

Call **`build_run_data`** once before `run_paper_experiment` (data is not duplicated inside the train/eval block).
