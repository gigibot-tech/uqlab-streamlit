# Feature docs

Small, focused reference docs for UQLab features. Most files here are intentionally short (under 200 lines) and link back to the canonical implementation files.

## Data & partitioning

| Doc | Topic |
|-----|-------|
| [data-pipeline.md](data-pipeline.md) | **Start here for data** — `build_run_data` |
| [dataset-plugin.md](dataset-plugin.md) | Dataset plugin contract |
| [four-region-partition.md](four-region-partition.md) | **Four-region split/noise** — data layer → `group` column |
| [four-region-notebook.md](four-region-notebook.md) | Six-step benchmark notebook (`uqlab_core`) |

## Evaluation & metrics

| Doc | Topic |
|-----|-------|
| [evaluation-pipeline.md](evaluation-pipeline.md) | **Start here for eval** — collect vs score |
| [evaluation-protocol.md](evaluation-protocol.md) | Train/eval/scoring today vs 4-region partition |
| [signal-registry.md](signal-registry.md) | EK-FAK signals pipeline |
| [registries.md](registries.md) | All registries (METRICS, perspectives, models) |
| [ATTRIBUTION_ARTIFACTS.md](ATTRIBUTION_ARTIFACTS.md) | `zwischen/` influence matrices + assignment notebook/YAML mapping |

## Sweeps & campaigns

| Doc | Topic |
|-----|-------|
| [disentanglement-benchmark.md](disentanglement-benchmark.md) | Paper metric + campaign plots |
| [sweep-grouping.md](sweep-grouping.md) | Post-run campaign grouping |
| [validation-sweeps.md](validation-sweeps.md) | Legacy + four-region sweep grids → metrics |
| [checkpoint-arsenal.md](checkpoint-arsenal.md) | Step 2.5 checkpoint review |
| [run-recovery.md](run-recovery.md) | Finalize failed runs from disk (`zwischen/`) |

## UI & workflow

| Doc | Topic |
|-----|-------|
| [workflow-config.md](workflow-config.md) | Wizard → YAML field mapping |
| [ui-debug.md](ui-debug.md) | Streamlit debug surfaces |
| [PAPER_FLOW.md](PAPER_FLOW.md) | Full run API map |

---

**Module READMEs:** [`src/uqlab_core/data/README.md`](../../src/uqlab_core/data/README.md) · [`src/uqlab_core/evaluation/README.md`](../../src/uqlab_core/evaluation/README.md)

**Architecture (start here):** [UQLAB_FLOW.md](../UQLAB_FLOW.md)
