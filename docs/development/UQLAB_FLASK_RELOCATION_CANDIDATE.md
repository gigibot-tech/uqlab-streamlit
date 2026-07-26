# Small-file relocation candidate: `uqlab-flask/`

## Folder checked

`uqlab-flask/` — a root-level Flask wizard UI.

## Why it was checked

The repository has several root-level directories. `uqlab-flask/` stands out because it is a self-contained, small application whose files are almost all under the 200/300 LoC threshold, while the rest of the root is dominated by the backend, the ML core, and project-wide configuration.

## Line-count inventory

| File | LoC |
|------|-----|
| `uqlab_flask/__init__.py` | 1 |
| `requirements.txt` | 2 |
| `uqlab_flask/templates/base.html` | 15 |
| `uqlab_flask/templates/step5.html` | 13 |
| `uqlab_flask/templates/sweep_not_found.html` | 13 |
| `uqlab_flask/templates/step4.html` | 18 |
| `uqlab_flask/templates/step1.html` | 25 |
| `uqlab_flask/templates/step3.html` | 25 |
| `uqlab_flask/templates/review.html` | 25 |
| `uqlab_flask/templates/step2.html` | 35 |
| `uqlab_flask/routes/__init__.py` | 0 |
| `app.py` | 37 |
| `README.md` | 33 |
| `uqlab_flask/routes/runs.py` | 139 |
| `uqlab_flask/static/style.css` | 177 |
| `uqlab_flask/routes/wizard.py` | 282 |
| `uqlab_flask/templates/launched.html` | 276 |
| `uqlab_flask/executor.py` | 652 |

**Summary:** 18 files total, 15 files under 200 LoC, 17 files under 300 LoC. Only `uqlab_flask/executor.py` exceeds 300 LoC.

## Current role

`uqlab-flask/` is a local, no-API Flask wizard that calls `uqlab.runner.execute.run_from_yaml` directly. It is referenced as an active entry point in:

- `START_HERE.md` — line 17
- `docs/UQLAB_FLOW.md` — line 159

## Can it be moved?

**Yes, but not by a simple drag-and-drop.**

The most natural relocation target is `frontend/uqlab-flask/`. That would align the root structure with `docs/development/ROOT_LEVEL_CLEANUP_ANALYSIS.md`, whose final target layout lists `frontend/` as a top-level directory.

### Why this is a candidate

- The folder is small and self-contained (routes, templates, static, executor).
- It is not imported by the backend, the Streamlit app, or the ML core — it is a standalone executable.
- Co-locating it under `frontend/` clarifies that it is a UI layer, separate from `backend/` and `src/`.

### What would need to change

1. **`uqlab-flask/app.py` hard-codes the project root** using `Path(__file__).resolve().parent.parent`. Moving the folder one level deeper (e.g. `frontend/uqlab-flask/app.py`) would break that assumption and must be updated.
2. **README / run instructions** in `uqlab-flask/README.md` and `START_HERE.md` need new paths and `PYTHONPATH` values.
3. **`docs/UQLAB_FLOW.md`** references `uqlab-flask/executor.py` and would need a path update.
4. Any tooling that globs root-level directories (e.g., `organize_root_scripts.sh`, packaging scripts) should be reviewed.

### Alternative targets

- `apps/uqlab-flask/` — explicit "application" directory, keeps UI code separate from library code.
- `archive/uqlab-flask/` — only if the Flask wizard is superseded and no longer maintained; references currently treat it as active, so archival is not recommended without confirmation.

## Recommendation

Move `uqlab-flask/` to `frontend/uqlab-flask/` and update the path assumptions in `app.py` plus the two documentation references. This is a **relocation candidate**; the actual move should be done in a follow-up change so imports and the local run path can be verified.
