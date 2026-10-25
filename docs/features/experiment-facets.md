# Experiment facets (four-region ↔ preference sets)

**Shared types:** [`src/uqlab/shared/experiment_ports.py`](../../src/uqlab/shared/experiment_ports.py)

Both UQ tracks expose **four named experimental axes** — the same framework slot (**Facet**), different physics:

| Track | Facet ids (SSOT) | Meaning | Train | Eval |
|-------|------------------|---------|-------|------|
| Classification | `noisy`, `sparse`, `clean`, `ood` ([`ALL_REGIONS`](../../src/uqlab/data/class_regions.py)) | Class partition + noise/sparsity | One model; region labels on eval | `group` / region packs |
| PrefSum | `faithfulness`, `coverage`, `joint`, `overall` ([`PREFERENCE_SET_NAMES`](../../src/uqlab/data/text_registry.py)) | Preference-pair rule | **One LoRA per set** | Scores / compare per adapter |

`FacetSpec` is a **view** over those SSOTs (`preference_set_facets()`, `class_region_facets()`), not a second catalog.

## DI ports (hexagonal)

```text
ExperimentPorts
  root        experiment / news project path
  data        DataPort      — list facets, load pairs / partitions
  training    TrainingPort  — start / continue training
  evaluation  EvalPort      — collect vs score by facet
```

- PrefSum injects [`PrefSumContracts`](../../src/uqlab/ui_components/workflow/prefsum/contracts.py) (subclass of `ExperimentPorts`) from [`streamlit_app_prefsum.py`](../../streamlit_app_prefsum.py).
- Classification wizard can adopt the same ports later; Step 3 regions = `list_facets()`.

## Collect vs score (PrefSum)

- **Collect / launch:** training port (`start_training`, `continue_and_evaluate`) and eval explain (`explain_llm_coverage` may write cache).
- **Score / read:** eval port tables (`article_places`, compare APIs) and saved metrics — same idea as [evaluation-pipeline.md](evaluation-pipeline.md).

## PrefSum pair-folder overlap (Training §1)

When the preference-folder selectbox changes, **DataPort** exposes:

| API | Role |
|-----|------|
| `pair_folder_metadata_overlap` | Selected jsonls × `article_split.json` (train/val/test) + Jaccard vs other `list_pair_sources` catalogs |
| `pair_dirs_article_overlap` | Two folders × shared preference-set names (Continue: section 1 vs checkpoint `pairs_path`) |
| `checkpoint_lineage` | `_plusN` continue graph + pair-folder → checkpoint edges (Mermaid); highlights selected folder |
| `checkpoint_test_overlap` | Eval/compare: checkpoint train pairs × test split (LEAK badge) |

UI: TrainingSection expanders **Overlap · selected pairs vs metadata** and **Lineage · checkpoints × pair folders**; ContinueSection warns when section 1 ≠ parent pair folder.

## Related

- [four-region-partition.md](four-region-partition.md)
- [text-summarization-registry.md](text-summarization-registry.md)
- [evaluation-protocol.md](evaluation-protocol.md)
