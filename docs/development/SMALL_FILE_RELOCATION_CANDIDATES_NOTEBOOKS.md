# Small File Relocation Candidates — `notebooks/`

**Branch**: `cursor/small-file-relocation-candidates-3a2d`  
**Date**: 2026-08-09  
**Scope**: Identify small files in the root-level `notebooks/` folder and determine whether they can be relocated.

---

## Executive Summary

The `notebooks/` folder at the repository root is a good relocation candidate for a small-file pass. It contains **22 files**, of which the *code* portions are all under **300 LoC** (and almost all under **200 LoC**). The `.ipynb` files look large in raw JSON terms, but their executable code cells are small.

The best relocation target is the **supporting Python code and documentation** that currently lives alongside the notebooks. These helpers belong in the core package or in the docs tree rather than in the notebook directory.

---

## Methodology

- **Threshold**: `< 200 LoC` (strong candidate) and `< 300 LoC` (still small).
- **Line count**: non-empty lines for `.py`/`.md` files; for `.ipynb` files we report both raw JSON lines and the smaller code-cell line count, because the JSON wrapper dominates the file size.
- **Excluded**: `.gitignore`, `.DS_Store`, and other non-source files.

## File inventory

| File | Total LoC | Code-cell LoC | Role | Candidate |
|------|----------:|--------------:|------|-----------|
| `notebooks/__init__.py` | 0 | — | Empty package marker | **Remove** |
| `notebooks/bootstrap_uqlab.py` | 64 | — | Notebook path bootstrap | **Move** |
| `notebooks/validation/__init__.py` | 0 | — | Empty package marker | **Remove** |
| `notebooks/validation/notebook_support_file.py` | 27 | — | Broken shim for `notebook_support` | **Remove** |
| `notebooks/validation/validation_functions.py` | 133 | — | Validation helpers | **Move** |
| `notebooks/validation/generate_consistency_notebook.py` | 129 | — | Legacy notebook generator | **Move / archive** |
| `notebooks/validation/PLOT_INTERPRETATION_GUIDE.md` | 92 | — | Markdown guide | **Move** |
| `notebooks/validation/METHOD_COMPARISON_PLOTS_README.md` | 121 | — | Markdown guide | **Move** |
| `notebooks/validation/CONSISTENCY_VALIDATION_README.md` | 195 | — | Markdown guide | **Move** |
| `notebooks/four_region_benchmark.ipynb` | 303 | 62 | Benchmark notebook | Keep |
| `notebooks/uncertainty_visualization_demo.ipynb` | 498 | 212 | Demo notebook | Keep |
| `notebooks/uncertainty_viz_3class.ipynb` | 521 | 233 | Demo notebook | Keep |
| `notebooks/validation/architecture_comparison_dataset_size.ipynb` | 305 | 139 | Validation notebook | Keep |
| `notebooks/validation/architecture_comparison_label_noise.ipynb` | 325 | 139 | Validation notebook | Keep |
| `notebooks/validation/logical_consistency_checks.ipynb` | 197 | 104 | Validation notebook | Keep |
| `notebooks/validation/logical_consistency_validation.ipynb` | 197 | 104 | Validation notebook | Keep |
| `notebooks/attribution_distribution_uncertainty.ipynb` | 787 | 169 | Analysis notebook | Keep |
| `notebooks/cifar10_paper_flow.ipynb` | 987 | 125 | Paper-flow notebook | Keep |
| `notebooks/resnet_baseline_experiment.ipynb` | 876 | 248 | Experiment notebook | Keep |
| `notebooks/watsonx_deployment_experiment.ipynb` | 867 | 346 | Deployment notebook | Keep |
| `notebooks/validation/RC9l Kopie.ipynb` | 1257 | 518 | Copy / archive notebook | Keep / archive |
| `notebooks/validation/build_consistency_notebook.py` | 440 | — | Notebook builder | Keep or move |
| `notebooks/validation/repair_validation_notebooks.py` | 434 | — | Notebook repair | Keep or move |

## Proposed relocation plan

### 1. Move supporting Python helpers into the core package

Create a new package `src/uqlab_core/notebooks/` (or `src/uqlab_core/notebook_utils/`) and move:

- `notebooks/bootstrap_uqlab.py` → `src/uqlab_core/notebooks/bootstrap_uqlab.py`
- `notebooks/validation/validation_functions.py` → `src/uqlab_core/notebooks/validation_functions.py`

These are small, importable modules used by notebooks. Keeping them in the package makes them version-controlled, testable, and importable without `sys.path` tricks.

### 2. Move notebook generators into `scripts/notebooks/`

- `notebooks/validation/build_consistency_notebook.py` → `scripts/notebooks/build_consistency_notebook.py`
- `notebooks/validation/generate_consistency_notebook.py` → `scripts/notebooks/generate_consistency_notebook.py`
- `notebooks/validation/repair_validation_notebooks.py` → `scripts/notebooks/repair_validation_notebooks.py`

These are execution scripts, not notebook content. They are larger than 300 LoC, so they are lower-priority than the helpers, but moving them keeps the `notebooks/` directory reserved for actual notebooks.

### 3. Move markdown guides into `docs/validation/`

- `notebooks/validation/PLOT_INTERPRETATION_GUIDE.md` → `docs/validation/PLOT_INTERPRETATION_GUIDE.md`
- `notebooks/validation/METHOD_COMPARISON_PLOTS_README.md` → `docs/validation/METHOD_COMPARISON_PLOTS_README.md`
- `notebooks/validation/CONSISTENCY_VALIDATION_README.md` → `docs/validation/CONSISTENCY_VALIDATION_README.md`

Documentation belongs in the `docs/` tree. The guides are already referenced by validation notebooks, so the references should be updated to the new paths.

### 4. Remove broken / empty artifacts

- `notebooks/__init__.py` (0 LoC) — `notebooks/` is not a Python package.
- `notebooks/validation/__init__.py` (0 LoC) — same reason.
- `notebooks/validation/notebook_support_file.py` (27 LoC) — the symlink it references (`notebooks/validation/notebook_support → ../../../src/walaris/notebook_support`) is broken, and the real `notebook_support` package is referenced elsewhere as `uqlab.notebook_support`. This shim is dead code.

### 5. Keep the `.ipynb` notebooks in place

The actual notebooks are content and should remain in `notebooks/` (or `notebooks/validation/`). They are small in terms of code cells and are the primary reason the folder exists.

## Files that should stay

| File / Group | Reason |
|--------------|--------|
| `.ipynb` notebooks | They are the content of the `notebooks/` folder. |
| `notebooks/validation/RC9l Kopie.ipynb` | Appears to be a copy; should be archived or deleted rather than relocated. |

## References to update if the moves are executed

- `src/uqlab_core/runner/notebook_run.py` looks for `notebooks/bootstrap_uqlab.py` in several candidate paths. If the bootstrap is moved into the package, this lookup can be simplified or removed.
- `notebooks/validation/CONSISTENCY_VALIDATION_README.md` and `METHOD_COMPARISON_PLOTS_README.md` reference `build_consistency_notebook.py`, `generate_consistency_notebook.py`, and `repair_validation_notebooks.py`. These references need to point to `scripts/notebooks/` after the move.
- Validation notebooks import `validation_functions` from the local directory. Those imports would need to become `from uqlab_core.notebooks.validation_functions import ...` once the module is in the package.

## Recommendation

1. **High priority**: remove the empty `__init__.py` files and the broken `notebook_support` shim. This is a safe, non-breaking cleanup.
2. **Medium priority**: move the small helpers (`bootstrap_uqlab.py`, `validation_functions.py`) into `src/uqlab_core/notebooks/` and update the import sites.
3. **Lower priority**: move the notebook generators and markdown guides into `scripts/notebooks/` and `docs/validation/` respectively. This is mostly cosmetic but keeps the `notebooks/` folder focused on actual notebooks.

---

*Generated by counting non-empty lines in every source/config file under `notebooks/`.*
