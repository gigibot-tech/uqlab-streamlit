# Small File Relocation Candidates

> Generated from branch `cursor/small-file-relocation-candidates-f581`.
> Focus: one root folder whose files are under 200–300 lines of code and could be relocated.

## Root folder selected: `scripts/`

`scripts/` is the most relocation-ready root folder:

- **56 total files** (code + shell + YAML), **45 of them ≤ 300 LoC** (80.4%).
- Many files are thin wrappers, one-off helpers, or examples that belong in the package they wrap.
- The existing `FINAL_ARCHITECTURE_DECISION.md` already mandates moving `scripts/runners/run_fast_*.py` into a `uqlab/cli/` package (status: *Final Decision - Ready for Implementation*).
- The actual ML package today is `uqlab_core` (not `uqlab`), so the decision needs to be mapped to the current layout.

---

## Top relocation candidates

### 1. `scripts/runners/run_fast.py` — 17 LoC (duplicate wrapper)

- **Current role**: convenience launcher that delegates to `run_fast_uncertainty_classification.py`.
- **Problem**: same file exists twice; `run_fast.py` adds no value except a shorter path.
- **Proposed action**: delete the wrapper; keep `run_fast_uncertainty_classification.py` as the canonical CLI.
- **Impact**: several docs mention `run_fast.py`; those references would need updating.

### 2. `scripts/runners/run_fast_uncertainty_classification.py` — 57 LoC

- **Current role**: canonical CLI entry point used by the FastAPI backend (`backend/app/core/ml_bootstrap.py:104`) and by examples.
- **Proposed location**: `src/uqlab_core/cli/run_fast.py` (or `src/uqlab/cli/run_fast.py` if the empty `src/uqlab/` shim is populated).
- **Why**: it is a thin argparse wrapper over `uqlab_core.runner.execute.run_from_yaml`. Thin CLIs belong inside the package they execute, not in a separate `scripts/` folder.
- **Impact**: backend must update its hard-coded path, and docs/START_HERE must switch to the new path.

### 3. `scripts/runners/` directory itself

- **Files**: only 3 files (`run_fast.py`, `run_fast_uncertainty_classification.py`, `run_validation_experiments.py`).
- **Proposed action**: after moving the two canonical runners into `src/uqlab_core/cli/`, the `scripts/runners/` folder can be removed.
- **Note**: `run_validation_experiments.py` is 644 LoC, so it is *not* a small-file candidate, but it is tightly coupled to the runners and should move with them into the CLI package.

### 4. `scripts/examples/*.py` — 103–233 LoC each

- **Files**: `example_cnn.py`, `example_dinov2.py`, `example_resnet.py`, `example_batch_sweep.py`, `minimal_experiment.py`.
- **Problem**: examples live as runnable scripts, but they are not reusable package code and are not tested as notebooks.
- **Proposed action**: move them to `notebooks/` as runnable `.ipynb` examples, or to a dedicated `examples/` folder at repo root. They are not production scripts and clutter `scripts/`.

### 5. `scripts/maintenance/` helpers — many under 100 LoC

- **Files**: `cleanup.sh`, `diagnose_rerun.py`, `diagnose_startup.py`, `remove_ui_debug.py`, `remove_walaris_references.py`, `run_dependency_analysis.sh`, `reorganize_folders.sh`, etc.
- **Observation**: most are small, single-purpose maintenance scripts. They can stay in `scripts/maintenance/` (that is the right place), but a few could be merged into a single `scripts/maintenance/repo_hygiene.py` toolkit if they are still run regularly.

---

## Secondary candidate: `uqlab-flask/`

- **5 code files, all ≤ 300 LoC** (the whole app is small).
- It is a standalone Flask wizard on port 5001 that duplicates the FastAPI backend + Streamlit frontend flow.
- **Options**:
  1. Keep as a lightweight local alternative (status quo).
  2. Move routes into `backend/app/` as a legacy-wizard blueprint and archive the templates.
  3. Convert to a notebook-based wizard if usage is low.
- No move is recommended without confirming active usage; it is noted here because it fits the “small root folder” pattern.

---

## Additional cleanup items found during analysis

1. **Empty `src/uqlab/` directory** — listed as a UV workspace member but contains no files. Either populate it as a shim re-exporting `uqlab_core` or remove it from `pyproject.toml` workspace members.
2. **Broken symlinks at root**:
   - `uq_classification -> src/uqlab/classification` (broken)
   - `uq_benchmarks -> src/uqlab/4_evaluation/benchmarks` (broken)
   - These should be removed or repointed to the current `uqlab_core` paths.

---

## Recommended next step

The lowest-risk, highest-value move is to consolidate the two duplicate runners in `scripts/runners/`:

1. Delete `scripts/runners/run_fast.py`.
2. Move `scripts/runners/run_fast_uncertainty_classification.py` to `src/uqlab_core/cli/run_fast.py` (create `src/uqlab_core/cli/` with an `__init__.py`).
3. Move `scripts/runners/run_validation_experiments.py` to `src/uqlab_core/cli/run_validation_experiments.py` so the CLI package stays together.
4. Update `backend/app/core/ml_bootstrap.py` to point to the new CLI path.
5. Update `START_HERE.md`, `README.md`, and `docs/features/*` paths that reference the old location.
6. Add a console-script entry in `src/uqlab_core/pyproject.toml` so `pip install uqlab-core` exposes `uqlab-run`.

This implements the already-approved architecture decision while adapting it to the current `uqlab_core` package name.
