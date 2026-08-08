# Small File Relocation Candidates — `src/uqlab_core` Root Audit

This audit checks the `src/uqlab_core` package root for code files under **200/300 LoC** and identifies whether they can be relocated to a more appropriate subdirectory.

## Analyzed folder

`src/uqlab_core/` (root of the ML core package)

## Thresholds

- **< 200 LoC**: strong relocation candidate when the file is a standalone utility.
- **< 300 LoC**: still small, but kept at root if it is package metadata or a documented entry point.

## Root-level code files found

| File | LoC | Threshold | Entry-point / documented | Relocation action |
|------|-----|-----------|--------------------------|-------------------|
| `README.md` | 39 | < 200 | Yes (package README) | **Kept at root** |
| `__init__.py` | 26 | < 200 | Yes (package marker) | **Kept at root** |
| `pyproject.toml` | 37 | < 200 | Yes (package metadata) | **Kept at root** |
| `runtime_paths.py` | 95 | < 200 | No (path utility) | **Moved to `src/uqlab_core/shared/runtime_paths.py`** |
| `results_io.py` | 404 | > 300 | Yes (results schema) | **Kept at root** |
| `run_artifacts.py` | 923 | > 300 | Yes (artifact loader) | **Kept at root** |

## Files moved

### `runtime_paths.py` → `src/uqlab_core/shared/`

- Purpose: persistent data locations (experiments, SQLite, caches) and repo-root resolution.
- Rationale: it is a small, self-contained utility that fits the `shared` subpackage alongside other common helpers (`shared/types.py`, `shared/config/`, `shared/utils/`). Keeping it at the package root mixes infrastructure concerns with the package's main results/artifact modules.
- Changes:
  - Updated `_REPO_ROOT` from `Path(__file__).resolve().parents[2]` to `parents[3]` so the repo root is still resolved correctly from the new location.
  - Updated imports in `src/uqlab_core/runner/experiment_core.py` and `src/uqlab_core/runner/execute.py` from `from uqlab_core.runtime_paths import repository_root` to `from uqlab_core.shared.runtime_paths import repository_root`.
- No other references found in the repo.

## Files kept at root and why

- `README.md`: package-level documentation belongs at the package root.
- `__init__.py`: required Python package marker.
- `pyproject.toml`: package metadata and build configuration; must stay at the package root for `uv`/`pip` resolution.
- `results_io.py` (404 LoC): defines the unified results schema and CSV adapters; a primary module of the package, above the relocation threshold.
- `run_artifacts.py` (923 LoC): loads and normalizes experiment artifacts; a primary module of the package, well above the relocation threshold.

## Follow-up candidates

The `src/uqlab_core/runner/` and `src/uqlab_core/evaluation/` subpackages contain many small modules and `__init__.py` files that could be candidates for further consolidation, but they are already organized under their respective functional areas and are not part of this root-level pass.
