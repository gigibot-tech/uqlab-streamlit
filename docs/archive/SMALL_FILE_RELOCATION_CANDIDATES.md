# Small File Relocation Candidates

**Date:** 2026-08-08  
**Branch:** `cursor/small-file-relocation-candidates-d0e2`  
**Scope:** Root-level folders with files under 200–300 lines of code and whether they can be relocated.

---

## Executive Summary

The root of the repository contains several small, focused folders. One folder stands out as a clear relocation candidate:

- **`uqlab-flask/`** — 18 files, 17 of which are under 300 LoC (94.4%), with a median size of 25 lines. It is a standalone Flask wizard that duplicates the experiment-launch surface already provided by the Streamlit UI and the FastAPI backend. It can be moved into a consolidated UI package or archived.

Other root folders also contain many small files, but they are already well-organized for their purpose (`configs/`, `scripts/`, `tests/`) or are actively maintained as the main backend (`backend/`). They are not recommended for relocation at this time.

---

## Methodology

A file was counted as "small" if it had fewer than 300 lines of code. A stricter threshold of 200 LoC was also recorded. Line counts exclude hidden files, `__pycache__`, and generated lockfiles such as `uv.lock`.

Root folders analyzed:

| Folder | Total files | <300 LoC | <200 LoC | Median LoC | Largest file |
|--------|-------------|----------|----------|------------|--------------|
| `uqlab-flask/` | 18 | 17 (94.4%) | 15 (83.3%) | 25 | `executor.py` (652) |
| `backend/` | 104 | 94 (90.4%) | 87 (83.7%) | 49 | `RUN_LABEL_NOISE_SWEEP_FLOW.md` (911) |
| `configs/` | 11 | 11 (100%) | 11 (100%) | 40 | `four_region_fashion_mlp.yaml` (64) |
| `scripts/` | 59 | 47 (79.7%) | 37 (62.7%) | 118 | `dependency_visualizer.py` (652) |
| `tests/` | 63 | 56 (88.9%) | 52 (82.5%) | 86 | `test_uncertainty_metrics.py` (473) |
| `notebooks/` | 23 | 11 (47.8%) | — | 303 | `validation/RC9l Kopie.ipynb` (1257) |
| `docs/` | 347 | 279 (80.4%) | — | 88 | `migration/BATCH_EXPERIMENTS_DESIGN.md` (1224) |

`configs/` is intentionally small by design (YAML files). `scripts/` and `tests/` were already reorganized in prior efforts ([`SCRIPTS_REORGANIZATION_COMPLETE.md`](./SCRIPTS_REORGANIZATION_COMPLETE.md), [`FOLDER_CONSOLIDATION_PLAN.md`](./FOLDER_CONSOLIDATION_PLAN.md)). `backend/` has a sound DDD structure documented in [`CODEBASE_STRUCTURE_AUDIT.md`](./CODEBASE_STRUCTURE_AUDIT.md).

---

## Primary Candidate: `uqlab-flask/`

### Current Structure

```text
uqlab-flask/
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

### Why It Stands Out

1. **Redundant UI surface.** The project already has a primary Streamlit UI (`streamlit_app_progressive.py`) and a FastAPI backend (`backend/`). `uqlab-flask/` is a third, local-only experiment launcher.
2. **Root-level clutter.** As a standalone top-level folder, it adds visual noise to the repository root and duplicates the `uqlab-` prefix already used by the main packages.
3. **Small enough to relocate cheaply.** With only 18 files and one non-trivial module, the move is low-risk.
4. **Clear boundaries.** It depends only on `uqlab.runner.execute.run_from_yaml` and `uqlab_orchestrator.run_spec` / `uqlab_orchestrator.config`. No circular dependencies are introduced by moving it.

### Current References

- `START_HERE.md` line 17: `Local Flask wizard (no API): [uqlab-flask/app.py](uqlab-flask/app.py) on :5001`
- `docs/UQLAB_FLOW.md` line 159: lists `uqlab-flask/executor.py` as the "Flask wizard" in the flow table.
- Internal imports inside `uqlab-flask/` itself.

---

## Relocation Options

### Option A: Move into a consolidated `ui/` root folder (Recommended)

Move both UI-related code pieces into a single root-level `ui/` folder:

```text
BEFORE:
streamlit_app_progressive.py
streamlit_requirements.txt
uqlab-flask/

AFTER:
ui/
├── streamlit/
│   ├── app.py              (from streamlit_app_progressive.py)
│   ├── requirements.txt    (from streamlit_requirements.txt)
│   └── components/         (future: from src/uqlab/ui_components per PACKAGE_REORGANIZATION_PROPOSAL.md)
└── flask/
    ├── app.py              (from uqlab-flask/app.py)
    ├── requirements.txt    (from uqlab-flask/requirements.txt)
    ├── uqlab_flask/
    │   ├── __init__.py
    │   ├── executor.py
    │   └── routes/
    ├── static/
    └── templates/
```

**Benefits:**
- All UI entry points live in one place.
- Removes `uqlab-` prefix duplication at the root.
- Aligns with the spirit of `PACKAGE_REORGANIZATION_PROPOSAL.md` (UI code separated from ML core).
- Keeps the Flask wizard intact for users who prefer it.

**Files to update:**
- `START_HERE.md` line 17.
- `docs/UQLAB_FLOW.md` line 159.
- Any shell scripts that launch the Flask app.

### Option B: Move into `src/` as `src/flask_ui/`

Fold the Flask wizard into the source tree alongside the ML core and orchestrator:

```text
src/
├── uqlab/                  (ML core)
├── uqlab_orchestrator/     (config transformation)
└── flask_ui/               (from uqlab-flask/)
    ├── app.py
    ├── requirements.txt
    ├── flask_ui/
    │   ├── __init__.py
    │   ├── executor.py
    │   └── routes/
    ├── static/
    └── templates/
```

**Benefits:**
- Treats the Flask UI as a first-class package.
- Imports can become relative (`from flask_ui.executor import ...`).

**Drawbacks:**
- Adds a UI dependency into `src/`, which contradicts the goal of keeping `src/` free of UI-specific code.
- The Flask app is an entry-point application, not a reusable library, so `src/` is a less natural home.

### Option C: Merge into `backend/`

Add a Flask frontend blueprint to the existing FastAPI backend.

**Drawbacks:**
- Mixes two web frameworks (FastAPI + Flask) in one folder.
- Increases backend dependency footprint.
- The Flask wizard is explicitly "no API"; merging it with the API backend muddles that distinction.

**Recommendation:** Not recommended.

### Option D: Keep as root folder but flatten the redundant nesting

Rename the root folder from `uqlab-flask/` to `flask-ui/` and drop the inner `uqlab_flask/` package, moving modules to the top level.

**Benefits:**
- Minimal change; no package renames beyond the folder.

**Drawbacks:**
- Does not solve the root-level clutter problem.
- `uqlab_flask` is a reasonable package name; flattening may hurt future growth.

**Recommendation:** Only if none of the other options are acceptable.

---

## Recommended Action

**Adopt Option A:** create a `ui/` root folder and move `uqlab-flask/` into `ui/flask/`. Defer moving the Streamlit app until the `ui_components` reorganization from `PACKAGE_REORGANIZATION_PROPOSAL.md` is executed, but structure `ui/` so both can coexist.

### Immediate Steps

1. Create `ui/flask/`.
2. Move `uqlab-flask/app.py`, `requirements.txt`, and the `uqlab_flask/` package into `ui/flask/`.
3. Update `sys.path` insertion in `app.py` if needed.
4. Update `START_HERE.md` and `docs/UQLAB_FLOW.md` references.
5. Verify the app still launches with `PYTHONPATH=src:ui/flask python ui/flask/app.py`.

### Deferred Steps

- When `PACKAGE_REORGANIZATION_PROPOSAL.md` is implemented, move `streamlit_app_progressive.py` and related UI code into `ui/streamlit/`.

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

## Risks

- **Import paths:** `uqlab-flask/app.py` manipulates `sys.path`. Any move must preserve the ability to import `uqlab` and `uqlab_orchestrator`.
- **Documentation links:** `START_HERE.md` and `docs/UQLAB_FLOW.md` contain hardcoded paths.
- **User habit:** External notes or bookmarks may reference `uqlab-flask/app.py`.
- **Templates/static paths:** `app.py` explicitly sets `template_folder` and `static_folder` using `FLASK_PKG / "uqlab_flask"`. These paths must be updated after the move.

---

## Conclusion

`uqlab-flask/` is the best small-file relocation candidate among root-level folders. It is small, self-contained, redundant with the existing UI/backend surfaces, and cheap to move. Consolidating it under a new `ui/` root folder improves repository organization without removing functionality.
