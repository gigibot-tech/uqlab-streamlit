# Paper API → UQLab mapping

Maps the Keras `InformationTheoreticModel` / `calculate_disentanglement_error` demo to UQLab modules and on-disk artifacts.

**If you only read one function:** [`run_experiment_core`](../../src/uqlab/runner/experiment_core.py) (or [`run_train_and_eval_phases`](../../src/uqlab/runner/train_eval.py) in notebooks).

## Single run (`run_experiment_core` or `run_train_and_eval_phases`)

| Paper (Keras) | UQLab | Module | Artifact |
|---|---|---|---|
| `model.fit(x, y)` | load + train | [`data/setup.py`](../../src/uqlab/data/setup.py) → [`data/packs.py`](../../src/uqlab/data/packs.py) + [`models/training.py`](../../src/uqlab/models/training.py) | `checkpoint.pt`, `training_data.csv` |
| MC → `expected_entropy`, `mutual_information` | MC dropout signals | [`runner/phases/eval.py`](../../src/uqlab/runner/phases/eval.py) `collect_uncertainty_signals` | `zwischen/01..05_*.pt`, `signal_table` in `results.pt` |
| `predict_disentangling(x)` | per-sample vectors | `score_uncertainty_signals` + bridge read | `per_sample_signals.csv`, `results.pt` |
| run record | summary dict | [`evaluation/reporting/run_summary.py`](../../src/uqlab/evaluation/reporting/run_summary.py) | `summary.json`, `summary.md`, `signal_formulas.json` |

### SAVE vs LOG (one run)

| Prefix / helper | stdout | disk |
|---|---|---|
| `print_experiment_configuration`, `log_run_data_context`, `log_run_complete` | yes | no |
| `save_zwischen_result` | no | `zwischen/*.pt` |
| `score_uncertainty_signals` | no | `per_sample_signals.csv` |
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

Same 3 cells as [`disentanglement_error/examples/CIFAR10_it_demo.ipynb`](../../disentanglement_error/examples/CIFAR10_it_demo.ipynb) — see [`notebooks/cifar10_paper_flow.ipynb`](../../notebooks/cifar10_paper_flow.ipynb).

After you have `config`, `run_cfg`, `data_pack`, `split_spec`, `device`:

```python
from uqlab.runner.train_eval import run_train_and_eval_phases

result = run_train_and_eval_phases(
    config=config,
    run_cfg=run_cfg,
    results_dir=results_dir,
    run_cache_dir=results_dir / "cache",
    data_pack=data_pack,
    split_spec=split_spec,
    device=device,
    seed=seed,
    training_config=config.training,
    data_config=config.data,
    model_config=config.model,
    eval_config=config.evaluation,
    ds_spec=run_cfg.dataset_spec,
    persist=True,   # False → no summary.json / results.pt
    log=True,
)
signal_table = result["signal_table"]
summary = result.get("summary")  # when persist=True
```

You still need **`prepare_experiment_data`** + **`prepare_run_data_context`** before this block (data loading is not duplicated inside `run_train_and_eval_phases`).
