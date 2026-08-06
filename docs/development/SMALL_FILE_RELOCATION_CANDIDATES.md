# Small File Relocation Candidates

Analysis of one root-level folder whose files are mostly below 200–300 lines of code, with an assessment of whether those files can be relocated.

## Folder Analyzed: `uqlab-flask/`

`uqlab-flask/` is a root-level Flask application that provides a local 5-step wizard UI for running uqlab experiments. It is documented in `START_HERE.md` as the "Local Flask wizard (no API)" running on port `:5001`.

### File Size Inventory

| File | Lines of Code | Below 200 LoC | Below 300 LoC | Notes |
|------|--------------:|---------------|---------------|-------|
| `uqlab_flask/routes/__init__.py` | 0 | ✅ | ✅ | Package marker (empty) |
| `uqlab_flask/__init__.py` | 1 | ✅ | ✅ | Package docstring only |
| `requirements.txt` | 2 | ✅ | ✅ | Flask dependencies |
| `uqlab_flask/templates/step5.html` | 13 | ✅ | ✅ | Wizard step template |
| `uqlab_flask/templates/sweep_not_found.html` | 13 | ✅ | ✅ | Error template |
| `uqlab_flask/templates/base.html` | 15 | ✅ | ✅ | Base template |
| `uqlab_flask/templates/step4.html` | 18 | ✅ | ✅ | Wizard step template |
| `uqlab_flask/templates/review.html` | 25 | ✅ | ✅ | Wizard step template |
| `uqlab_flask/templates/step1.html` | 25 | ✅ | ✅ | Wizard step template |
| `uqlab_flask/templates/step3.html` | 25 | ✅ | ✅ | Wizard step template |
| `README.md` | 33 | ✅ | ✅ | App-specific README |
| `uqlab_flask/templates/step2.html` | 35 | ✅ | ✅ | Wizard step template |
| `app.py` | 37 | ✅ | ✅ | Flask app factory / entry point |
| `uqlab_flask/routes/runs.py` | 139 | ✅ | ✅ | API routes for sweep status/plots |
| `uqlab_flask/static/style.css` | 177 | ✅ | ✅ | App styles |
| `uqlab_flask/templates/launched.html` | 276 | ✅ | ❌ | Results dashboard template |
| `uqlab_flask/routes/wizard.py` | 282 | ✅ | ❌ | Wizard page routes |
| `uqlab_flask/executor.py` | 652 | ❌ | ❌ | Sweep execution engine |
| **Total** | **1,768** | | | |

*13 of 18 files are below 200 LoC; 15 of 18 are below 300 LoC.*

### Can the Small Files Be Moved?

**Verdict: No, not individually.**

The small files in `uqlab-flask/` are tightly coupled parts of a single Flask application:

- `app.py` registers the blueprints from `routes/` and points to the `templates/` and `static/` folders.
- `routes/wizard.py` and `routes/runs.py` import from `uqlab_flask.executor`.
- Every HTML template extends `base.html` and is rendered by a route in `wizard.py` or `runs.py`.
- `requirements.txt` and `README.md` belong to the app as a whole.
- The empty `__init__.py` files are required package markers.

Moving any of these files independently would break imports, template resolution, or static asset paths. The only relocation unit is the entire `uqlab-flask/` directory.

### Whole-Folder Relocation Options Considered

| Destination | Assessment |
|-------------|------------|
| `apps/uqlab-flask/` | Logical for a standalone app, but no `apps/` convention exists in the repo. |
| `examples/uqlab-flask/` | Would imply it is example code, but `START_HERE.md` presents it as a current run option. |
| `archive/uqlab-flask/` or `legacy/uqlab-flask/` | Would imply deprecation, but the folder is still referenced as a current UI option. |
| `backend/uqlab-flask/` | Inappropriate — `backend/` is the FastAPI service; mixing Flask here violates separation of concerns. |
| `src/uqlab_flask/` | Would turn it into a library package, but it is an executable app with templates/static assets, not a reusable package. |

### Recommendation

Keep `uqlab-flask/` at the repository root. The files are small because they are split along the natural boundaries of a Flask app (routes, templates, static assets, executor), but they are not independent relocation candidates. The folder itself is a cohesive, runnable application and is documented as a supported UI option.

### References That Would Need Updating on Any Move

If the folder is ever relocated as a whole unit, the following references must be updated:

- `START_HERE.md` line 17 (`uqlab-flask/app.py`)
- `docs/UQLAB_FLOW.md` table entry for the Flask wizard
- `uqlab-flask/README.md` run commands
- `uqlab-flask/app.py` path assumptions (`PROJECT_ROOT`, `EXPERIMENTS_DIR`, `template_folder`, `static_folder`)

## Other Root Folders Briefly Reviewed

- `configs/` — All files are below 100 LoC, but the folder is referenced by CLI scripts, notebooks, and documentation across the project. The existing `ROOT_LEVEL_CLEANUP_ANALYSIS.md` already marks `configs/` as a root folder to keep.
- `data/` — Only contains a `.gitkeep` file; not a relocation candidate.
- `.vscode/` — Small IDE configuration files; standard location, should not move.

