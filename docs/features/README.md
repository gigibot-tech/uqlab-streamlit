# Feature docs

Small, focused feature specifications grouped by subsystem.

## Data

| Doc | Topic |
|-----|--------|
| [data-pipeline.md](data/data-pipeline.md) | **Start here for data** — `build_run_data` |
| [four-region-partition.md](data/four-region-partition.md) | **Four-region split/noise** — data layer → `group` column |
| [dataset-plugin.md](data/dataset-plugin.md) | Dataset plugin contract |
| [four-region-notebook.md](data/four-region-notebook.md) | Six-step benchmark notebook (`uqlab_core`) |

## Evaluation

| Doc | Topic |
|-----|--------|
| [evaluation-pipeline.md](evaluation/evaluation-pipeline.md) | **Start here for eval** — collect vs score |
| [evaluation-protocol.md](evaluation/evaluation-protocol.md) | Train/eval/scoring today vs 4-region partition |
| [disentanglement-benchmark.md](evaluation/disentanglement-benchmark.md) | Paper metric + campaign plots |
| [validation-sweeps.md](evaluation/validation-sweeps.md) | Legacy + four-region sweep grids → metrics |
| [signal-registry.md](evaluation/signal-registry.md) | EK-FAK signals pipeline |
| [ATTRIBUTION_ARTIFACTS.md](evaluation/ATTRIBUTION_ARTIFACTS.md) | `zwischen/` influence matrices + assignment notebook/YAML mapping |

## Operations

| Doc | Topic |
|-----|--------|
| [registries.md](operations/registries.md) | All registries (METRICS, perspectives, models) |
| [sweep-grouping.md](operations/sweep-grouping.md) | Post-run campaign grouping |
| [checkpoint-arsenal.md](operations/checkpoint-arsenal.md) | Step 2.5 checkpoint review |
| [run-recovery.md](operations/run-recovery.md) | Finalize failed runs from disk (`zwischen/`) |

## UI

| Doc | Topic |
|-----|--------|
| [workflow-config.md](ui/workflow-config.md) | Wizard → YAML field mapping |
| [ui-debug.md](ui/ui-debug.md) | Streamlit debug surfaces |

## Paper

| Doc | Topic |
|-----|--------|
| [PAPER_FLOW.md](paper/PAPER_FLOW.md) | Full run API map |

**Module READMEs:** [`src/uqlab_core/data/README.md`](../../src/uqlab_core/data/README.md) · [`src/uqlab_core/evaluation/README.md`](../../src/uqlab_core/evaluation/README.md)

**Architecture (start here):** [UQLAB_FLOW.md](../UQLAB_FLOW.md)
