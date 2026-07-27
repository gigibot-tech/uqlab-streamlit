# Small-File Relocation Candidate: `uqlab-flask/`

## Executive Summary

`uqlab-flask/` is a root-level Flask application that provides a local 5-step HTML wizard for running uncertainty experiments. It is small (5 Python files, ~1,111 lines total), self-contained, and has no external imports from the rest of the repository. These qualities make it a good candidate for relocation or consolidation.

## Candidate Folder

| Folder | Role | Total Python Files | Total Python LoC |
|--------|------|-------------------|------------------|
| `uqlab-flask/` | Local Flask wizard UI + embedded sweep executor | 5 | 1,111 |

## File Inventory

| File | LoC | Responsibility | Under 300 LoC |
|------|-----|----------------|---------------|
| `app.py` | 37 | Flask app factory and bootstrap | Yes |
| `uqlab_flask/__init__.py` | 1 | Package marker | Yes |
| `uqlab_flask/routes/runs.py` | 139 | JSON API for runs/sweeps/status | Yes |
| `uqlab_flask/routes/wizard.py` | 282 | 5-step HTML wizard routes | Yes |
| `uqlab_flask/executor.py` | 652 | In-memory job/sweep queue and runner | No |

**Summary:** 4 of 5 files are under 300 LoC; the only large file is the executor that wraps `uqlab.runner.execute.run_from_yaml`.

## External Coupling

**Imports into `uqlab-flask` from the rest of the repo:**

```python
# routes/runs.py
from uqlab_orchestrator.run_spec import build_run_yaml, validate_run_yaml

# routes/wizard.py
from uqlab_orchestrator.config import default_workflow, merge_workflow_defaults

# executor.py
from uqlab.runner.execute import run_from_yaml as pipeline_run

# routes/wizard.py (plot endpoint)
from uqlab.evaluation.reporting.sweep_line_plot import build_sweep_line_plot
```

**Imports from the rest of the repo into `uqlab-flask`:** none found.

**References to `uqlab-flask` or `uqlab_flask` in the repo:**

- `START_HERE.md` — mentions `uqlab-flask/app.py` as a local Flask wizard on port 5001
- `uqlab-flask/README.md` — local README for the app
- `docs/UQLAB_FLOW.md` — lists `uqlab-flask/executor.py` as a consumer of `run_from_yaml`

**Risk assessment:** Low. The app is standalone and only consumes public API surfaces from `uqlab_orchestrator` and `uqlab.runner`.

## Relocation Options

### Option A: Keep at root, rename to `flask-wizard/`

- **Pros:** Minimal change; name better reflects purpose.
- **Cons:** Still a root-level application folder; does not reduce root clutter.

### Option B: Move into `backend/` as `backend/flask_wizard/`

- **Pros:** Consolidates all web-facing entry points under `backend/`; easy to share the same `experiments_dir` and Docker network conventions.
- **Cons:** Mixes FastAPI and Flask idioms; the backend has its own dependency set (`backend/pyproject.toml` vs. `uqlab-flask/requirements.txt`).

### Option C: Move into `src/uqlab_flask/`

- **Pros:** Aligns with the package-oriented layout used by `src/uqlab/` and `src/uqlab_orchestrator/`.
- **Cons:** `uqlab-flask` is an executable app, not a reusable library; putting it in `src/` may blur the boundary between library code and application code.

### Option D: Move to `tools/flask-wizard/`

- **Pros:** Clearly separates auxiliary tools from the core ML library, orchestrator, and backend; matches the standalone nature of the app.
- **Cons:** Introduces a new top-level folder; requires updating documentation paths and the `app.py` path logic.

## Recommendation

**Option D — move `uqlab-flask/` to `tools/flask-wizard/`** is the cleanest long-term choice. It keeps the app at the repository root for discoverability, but groups it with other non-library, non-backend tools rather than leaving it as a sibling of `src/`, `backend/`, and `scripts/`.

If the team prefers not to introduce a new root folder, **Option B** (`backend/flask_wizard/`) is a reasonable alternative because the Flask wizard is ultimately another web-facing entry point.

## Migration Checklist (if moving to `tools/flask-wizard/`)

1. Create `tools/flask-wizard/` and move `uqlab-flask/` contents there.
2. Update `tools/flask-wizard/app.py` to compute `ROOT`, `SRC`, and `FLASK_PKG` relative to the new location.
3. Update `START_HERE.md` and `docs/UQLAB_FLOW.md` to reference the new path.
4. Update `uqlab-flask/README.md` (or relocate it to `tools/flask-wizard/README.md`) and fix the run command.
5. Verify `PYTHONPATH` requirements and `requirements.txt` paths still work.
6. Run a smoke test with `python tools/flask-wizard/app.py` and confirm the wizard still launches.
7. Remove the empty `uqlab-flask/` directory.

## Next Steps

- Decide on Option A, B, C, or D.
- If the team agrees, execute the migration and update the references above.
