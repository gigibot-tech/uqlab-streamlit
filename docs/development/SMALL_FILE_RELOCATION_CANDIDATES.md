# Small File Relocation Candidates

**Branch**: `cursor/small-file-relocation-candidates-2215`  
**Date**: 2026-07-27  
**Scope**: Identify one root-level folder whose files are mostly < 200/300 LoC and determine whether they can be relocated.

---

## Executive Summary

After scanning every root-level directory, **`scripts/`** stands out as the best candidate for further relocation. It currently contains **47 files under 300 LoC** (37 of them under 200 LoC). Many of these are small CLI wrappers, examples, and analysis utilities that logically belong inside the source packages (`src/uqlab_core/`, `backend/`, etc.) rather than in a loose top-level scripts directory.

A second, more compact candidate is **`uqlab-flask/`**, a small Flask application with 17 files, 15 of which are under 200 LoC. It could be relocated as a whole unit (e.g., to `src/legacy/uqlab_flask/` or `backend/legacy/`).

---

## Methodology

- Threshold: **< 300 LoC** (with **< 200 LoC** highlighted as strong relocation candidates).
- Excluded: docs, tests, and backend internals, because small files there are usually intentional (`__init__.py`, route files, migration stubs, etc.).
- Focused on code that is standalone and not tightly coupled to the root-level folder it lives in.

---

## Root-Level Folder Overview

| Folder | Files < 300 LoC | Files < 200 LoC | Relocation Potential |
|--------|----------------:|----------------:|----------------------|
| `docs/` | 279 | 231 | Low — documentation is naturally small |
| `backend/` | 104 | 97 | Low — FastAPI structure is already idiomatic |
| `tests/` | 56 | 52 | Low — tests are naturally small |
| `src/` | 48 | 37 | Low — mostly `__init__.py` and package glue |
| **`scripts/`** | **47** | **37** | **High — many are standalone wrappers** |
| `uqlab-flask/` | 17 | 15 | Medium — whole app could move |
| `configs/` | 11 | 11 | Low — YAML configs are naturally small |
| `notebooks/` | 11 | 10 | Low — notebooks are naturally self-contained |
| `data/` | 1 | 1 | Low — just `.gitkeep` |

---

## `scripts/` — Primary Candidate

### Current Subfolders

```
scripts/
├── analysis/          # 5 small analysis scripts
├── deployment/        # 6 shell scripts (run Streamlit, deploy, test API)
├── examples/          # 5 example Python scripts
├── lib/               # 10 shared shell libraries (intentional, keep)
├── maintenance/       # 13 diagnostics / cleanup / migration scripts
├── runners/           # 3 small runner wrappers
├── setup/             # 7 setup / reporting scripts
├── migrate_to_uqlab_core.py
├── regenerate_shims.py
├── validate_per_class_campaign.py
└── README.md          # 637 LoC, deployment-focused doc
```

### Strong Relocation Candidates (< 200 LoC)

| File | LoC | Current Role | Proposed Home | Rationale |
|------|----:|--------------|---------------|-----------|
| `scripts/runners/run_fast.py` | 17 | CLI experiment runner | `src/uqlab_core/cli/run_fast.py` | Thin wrapper around the execution engine; belongs in the package CLI |
| `scripts/runners/run_fast_uncertainty_classification.py` | 57 | Legacy CLI runner | `src/uqlab_core/cli/run.py` or archive | Already identified in `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` as a CLI candidate |
| `scripts/runners/run_validation_experiments.py` | ? | Validation runner | `src/uqlab_core/cli/run_validation.py` | Same pattern as above |
| `scripts/examples/example_cnn.py` | 118 | CNN usage example | `src/uqlab_core/examples/cnn.py` | Examples should live with the package they demonstrate |
| `scripts/examples/example_resnet.py` | 130 | ResNet usage example | `src/uqlab_core/examples/resnet.py` | Same as above |
| `scripts/examples/example_dinov2.py` | 103 | DINOv2 usage example | `src/uqlab_core/examples/dinov2.py` | Same as above |
| `scripts/examples/example_batch_sweep.py` | 233 | Batch sweep example | `src/uqlab_core/examples/batch_sweep.py` | Slightly larger but still example code |
| `scripts/examples/minimal_experiment.py` | 221 | Minimal experiment | `src/uqlab_core/examples/minimal_experiment.py` | Entry-point style example |
| `scripts/analysis/four_region_validation.py` | 90 | Analysis script | `src/uqlab_core/analysis/four_region_validation.py` | Analysis code belongs with the analysis package |
| `scripts/analysis/paper_benchmarks.py` | 105 | Benchmark analysis | `src/uqlab_core/analysis/paper_benchmarks.py` | Same as above |
| `scripts/analysis/disentanglement_error.py` | 274 | Error analysis | `src/uqlab_core/analysis/disentanglement_error.py` | Same as above |
| `scripts/analysis/analyze_my_run.py` | ? | Run inspection | `src/uqlab_core/analysis/run_inspector.py` | Same as above |
| `scripts/analysis/plot_run_region_means.py` | 114 | Plotting utility | `src/uqlab_core/analysis/plot_run_region_means.py` | Same as above |
| `scripts/setup/download_cifar10n.py` | 40 | Dataset downloader | `src/uqlab_core/data/download_cifar10n.py` | Data utility belongs in the data package |
| `scripts/setup/validate_architectures.py` | 60 | Architecture validator | `src/uqlab_core/models/validate_architectures.py` | Model-related validation |
| `scripts/setup/generate_campaign_report.py` | 117 | Report generator | `src/uqlab_core/reporting/generate_campaign_report.py` | Reporting concern |
| `scripts/setup/generate_campaign_config_timeline.py` | 124 | Timeline generator | `src/uqlab_core/reporting/generate_campaign_config_timeline.py` | Same as above |
| `scripts/setup/generate_thesis_diagram.py` | 140 | Diagram generator | `src/uqlab_core/reporting/generate_thesis_diagram.py` | Same as above |
| `scripts/setup/report_unified.py` | 76 | Unified report | `src/uqlab_core/reporting/report_unified.py` | Same as above |
| `scripts/setup/calculate_ude_scores.py` | ? | Metric calculation | `src/uqlab_core/evaluation/calculate_ude_scores.py` | Evaluation utility |

### What Should Stay in `scripts/`

| File / Group | Reason |
|--------------|--------|
| `scripts/lib/*.sh` | These are shared shell libraries used by deployment scripts; they are intentionally centralized. |
| `scripts/deployment/*.sh` | DevOps scripts are fine at the project root. |
| `scripts/maintenance/*` | One-off cleanup, migration, and diagnostic scripts belong in a maintenance bucket. |
| `scripts/README.md` | Could be split into a deployment README and a scripts README, but it is documentation, not code. |

### Migration Plan (High-Level)

1. **Create new package homes** (if they don't exist):
   - `src/uqlab_core/cli/` — for runner scripts.
   - `src/uqlab_core/examples/` — for example scripts.
   - `src/uqlab_core/analysis/` — for analysis scripts.
   - `src/uqlab_core/reporting/` — for report/diagram generators.
   - `src/uqlab_core/data/download/` — for dataset downloaders.

2. **Move files with import path updates**:
   - Update any `sys.path` manipulation to use package imports instead.
   - Add `pyproject.toml` entry points or console scripts so runners remain runnable from the command line.

3. **Archive or delete true one-offs**:
   - `scripts/maintenance/remove_walaris_references.py` and similar migration scripts are probably one-time use and could be archived.

4. **Update documentation**:
   - Update `README.md` and any user guides that reference `scripts/runners/...` or `scripts/examples/...`.

---

## `uqlab-flask/` — Secondary Candidate

This is a small, self-contained Flask UI. If the project is moving toward Streamlit as the primary UI, the entire folder could be:

- **Archived** to `src/legacy/uqlab_flask/` or `dead_code/uqlab_flask/` if it is no longer maintained.
- **Moved into `backend/`** if it is meant to be a lightweight web UI companion to the FastAPI backend.
- **Kept** but relocated to `src/uqlab_flask/` so it is no longer a root-level outlier.

Because the decision depends on product strategy (keep Flask vs. deprecate it), it is flagged as a secondary candidate rather than the primary focus.

---

## Recommendation

1. **Primary action**: Focus on `scripts/` and relocate the small runner, example, and analysis scripts into the appropriate `src/uqlab_core/` subpackages. This directly implements the separation of concerns described in `ARCHITECTURE_IMPROVEMENT_PROPOSAL.md` and `PACKAGE_REORGANIZATION_PROPOSAL.md`.
2. **Secondary action**: Decide the fate of `uqlab-flask/` (archive, move, or keep) and execute that decision.
3. **Avoid moving**: docs, tests, backend internals, and `scripts/lib/` because they are already well-placed or intentionally centralized.

---

## Generated By

Analysis script: `/tmp/analyze_root_folders.py` (line-count + heuristic relocation suggestions).
