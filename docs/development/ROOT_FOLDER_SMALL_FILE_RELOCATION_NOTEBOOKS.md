# Root Folder Small-File Relocation Analysis: `notebooks/`

**Date**: 2026-09-17  
**Branch**: `cursor/small-file-relocation-candidates-4541`  
**Scope**: One root folder whose files are under the 200/300 LoC threshold.

---

## Folder Analyzed

```
notebooks/
├── __init__.py              # 0 LoC
├── bootstrap_uqlab.py       # 63 LoC
└── ... (subdirectories with notebook files)
```

Direct files in the root of `notebooks/` are well below the 200/300 LoC limit.

## File Responsibilities

### `bootstrap_uqlab.py`
- Adds the repository `src/` directory to `sys.path` so that `import uqlab` / `import uqlab_core` works when notebooks are opened from arbitrary working directories.
- Searches upward from the current working directory for repo roots named `uqlab-streamlit` or `four-region-benchmark`.

### `__init__.py`
- Empty marker that makes `notebooks/` importable as a Python package.

## Why the Files Can Be Moved

1. **`bootstrap_uqlab.py` is not notebook content** — it is a runtime path/bootstrap utility.
2. **It is already a dependency of the core runner** — `src/uqlab_core/runner/notebook_run.py` discovers and executes this file by path.
3. **No notebook imports it directly** — grep across `notebooks/` shows only the file itself references the bootstrap module.
4. **No tests reference it** — `tests/` has no dependencies on the bootstrap file.
5. **Consolidating into `uqlab_core.runner`** removes the cross-directory file execution and makes the bootstrap a normal import.

## Proposed Relocation

```
notebooks/bootstrap_uqlab.py
    ↓
src/uqlab_core/runner/notebook_bootstrap.py
```

### Changes required

1. Move the file.
2. Remove the self-referential `find_bootstrap_file()` / `load_bootstrap_module()` helpers (they become unnecessary once the module is importable).
3. In `src/uqlab_core/runner/notebook_run.py`, replace the file-discovery + `exec_module` block with a direct import:

```python
from uqlab_core.runner.notebook_bootstrap import ensure_uqlab_path
```

4. Keep `notebooks/__init__.py` in place so the directory remains a package if anything still treats it as such.

## Benefits

- Removes fragile path-based file execution from the core runner.
- Bootstrap logic is now versioned alongside the runner it supports.
- `notebooks/` becomes purely notebook content rather than a mix of notebooks and setup scripts.

## Risks / Mitigations

- **External notebooks that manually locate `notebooks/bootstrap_uqlab.py`**: None found in the repo; if any exist outside the repo, they would need to update their path.
- **Import order**: Because `notebook_run.py` already lives inside `uqlab_core.runner`, importing `notebook_bootstrap` from the same package is safe.
