# Small File Relocation Candidates

**Date:** 2026-08-10
**Branch:** `cursor/small-file-relocation-candidates-0ed2`
**Scope:** Root-level folders with files under 200–300 lines of code and whether they can be relocated.

---

## Executive Summary

The root of the repository contains several small, focused folders. One folder stood out as a clear relocation candidate and has now been moved:

- **`uqlab-flask/`** → **`ui/flask/`** — 18 files, 17 of which were under 300 LoC (94.4%), with a median size of 25 lines. It was a standalone Flask wizard that duplicated the experiment-launch surface already provided by the Streamlit UI and the FastAPI backend. Consolidating it under a new `ui/` root folder removes root-level clutter and groups all UI entry points together.

Other root folders also contain many small files, but they are already well-organized for their purpose (`configs/`, `scripts/`, `tests/`) or are actively maintained as the main backend (`backend/`). They are not recommended for relocation at this time.

---

## Methodology

A file was counted as "small" if it had fewer than 300 lines of code. A stricter threshold of 200 LoC was also recorded. Line counts exclude hidden files, `__pycache__`, and generated lockfiles such as `uv.lock`.

Root folders analyzed:

| Folder | Total files | <300 LoC | <200 LoC | Median LoC | Largest file |
|--------|-------------|----------|----------|------------|--------------|
| `uqlab-flask/` (now `ui/flask/`) | 18 | 17 (94.4%) | 15 (83.3%) | 25 | `executor.py` (652) |
| `backend/` | 104 | 94 (90.4%) | 87 (83.7%) | 49 | `RUN_LABEL_NOISE_SWEEP_FLOW.md` (911) |
| `configs/` | 11 | 11 (100%) | 11 (100%) | 40 | `four_region_fashion_mlp.yaml` (64) |
| `scripts/` | 59 | 47 (79.7%) | 37 (62.7%) | 118 | `dependency_visualizer.py` (652) |
| `tests/` | 63 | 56 (88.9%) | 52 (82.5%) | 86 | `test_uncertainty_metrics.py` (473) |
| `notebooks/` | 23 | 11 (47.8%) | — | 303 | `validation/RC9l Kopie.ipynb` (1257) |
| `docs/` | 347 | 279 (80.4%) | — | 88 | `migration/BATCH_EXPERIMENTS_DESIGN.md` (1224) |

`configs/` is intentionally small by design (YAML files). `scripts/` and `tests/` were already reorganized in prior efforts ([`SCRIPTS_REORGANIZATION_COMPLETE.md`](./SCRIPTS_REORGANIZATION_COMPLETE.md), [`FOLDER_CONSOLIDATION_PLAN.md`](./FOLDER_CONSOLIDATION_PLAN.md)). `backend/` has a sound DDD structure documented in [`CODEBASE_STRUCTURE_AUDIT.md`](./CODEBASE_STRUCTURE_AUDIT.md).

---

## Relocation Performed: `uqlab-flask/` → `ui/flask/`

### New Structure

```text
ui/flask/
├── app.py                          37 LoC — application factory
├── README.md                       33 LoC — run instructions
├── requirements.txt                 2 LoC — Flask dependencies
└── uqlab_flask/
    ├── __init__.py                  1 LoC
    ├── executor.py                652 LoC — background sweep worker
    ├── routes/
    │   ├── __init__.py              0 LoC
    │   ├── runs.py                139 LoC — JSON API endpoints
    │   └── wizard.py              282 LoC — 5-step HTML wizard
    ├── static/
    │   └── style.css              177 LoC
    └── templates/
        ├── base.html               15 LoC
        ├── launched.html          276 LoC
        ├── review.html             25 LoC
        ├── step1.html              25 LoC
        ├── step2.html              35 LoC
        ├── step3.html              25 LoC
        ├── step4.html              18 LoC
        ├── step5.html              13 LoC
        └── sweep_not_found.html    13 LoC
```

Only `executor.py` exceeds 300 LoC. All other Python, HTML, CSS, and config files are well below the threshold.

### Why It Was Moved

1. **Redundant UI surface.** The project already has a primary Streamlit UI (`streamlit_app_progressive.py`) and a FastAPI backend (`backend/`). `uqlab-flask/` was a third, local-only experiment launcher.
2. **Root-level clutter.** As a standalone top-level folder, it added visual noise to the repository root and duplicated the `uqlab-` prefix already used by the main packages.
3. **Small enough to relocate cheaply.** With only 18 files and one non-trivial module, the move was low-risk.
4. **Clear boundaries.** It depends only on `uqlab.runner.execute.run_from_yaml` and `uqlab_orchestrator.run_spec` / `uqlab_orchestrator.config`. No circular dependencies were introduced by moving it.

### Changes Made

- Created `ui/flask/` and moved `uqlab-flask/app.py`, `requirements.txt`, `README.md`, and the `uqlab_flask/` package into it.
- Updated `ui/flask/app.py` so that `ROOT` resolves to the repository root (`Path(__file__).resolve().parent.parent.parent`).
- Updated `ui/flask/README.md` run instructions to use the new paths.
- Updated `START_HERE.md` to reference `ui/flask/app.py`.
- Updated `docs/UQLAB_FLOW.md` to reference `ui/flask/uqlab_flask/executor.py`.

### Verification

Launch command after the move:

```bash
cd uqlab-streamlit
pip install -r ui/flask/requirements.txt
PYTHONPATH=src:ui/flask python ui/flask/app.py
```

Internal imports inside `uqlab_flask/` remain unchanged because `app.py` inserts `FLASK_PKG` into `sys.path` at startup.

---

## Other Root Folders Considered and Rejected

| Folder | Reason not to relocate |
|--------|------------------------|
| `backend/` | Already follows DDD; small files are scripts, config, and legacy shims that should be migrated gradually, not in one move. |
| `configs/` | YAML files are intentionally small; no relocation benefit. |
| `scripts/` | Already reorganized; each subfolder has a clear purpose and healthy file count. |
| `tests/` | Small test files are normal; moving them would break the existing test layout. |
| `notebooks/` | Mixed sizes; large notebooks dominate. Not a relocation candidate. |
| `docs/` | Documentation is intentionally granular. |

---

## Future Work

- When `PACKAGE_REORGANIZATION_PROPOSAL.md` is implemented, move `streamlit_app_progressive.py` and related UI code into `ui/streamlit/` so that both UI entry points live under a single `ui/` root folder.

---

## Risks Addressed

- **Import paths:** `app.py` manipulates `sys.path`. The `ROOT` adjustment ensures `uqlab` and `uqlab_orchestrator` are still discoverable.
- **Documentation links:** `START_HERE.md` and `docs/UQLAB_FLOW.md` were updated.
- **Templates/static paths:** `app.py` sets `template_folder` and `static_folder` using `FLASK_PKG / "uqlab_flask"`. Because `FLASK_PKG` now resolves to `ui/flask`, the nested `uqlab_flask` template/static directories are still found correctly.

---

## Conclusion

`uqlab-flask/` was the best small-file relocation candidate among root-level folders. It was small, self-contained, redundant with the existing UI/backend surfaces, and cheap to move. Consolidating it under `ui/flask/` improves repository organization without removing functionality.
