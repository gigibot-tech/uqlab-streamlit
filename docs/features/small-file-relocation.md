# Small file relocation candidates

## Goal
Find a root-level folder whose files are small enough (≲ 300 LoC) that the folder could be relocated into a more appropriate package, then execute one relocation.

## Candidate folders analyzed

| Folder | Python files | Max LoC | Notes |
|--------|-------------|---------|-------|
| `scripts/runners/` | 3 | 643 | Two files are tiny (17, 57 LoC) but `run_validation_experiments.py` is 643 LoC and is actively spawned by the backend. Relocation is invasive. |
| `uqlab-flask/` | 5 + templates | 652 | `app.py`, `routes/runs.py`, `routes/wizard.py` and all templates are < 300 LoC. Only `executor.py` is large. It is a documented optional local Flask wizard. It currently imports the old `uqlab` package (which is empty), so it is also broken. |
| `backend/app/core/` | 5 | 147 | All files < 300 LoC, but this is a backend sub-package, not a root folder. |
| `src/uqlab/` | 0 | - | Empty workspace member; no files to move. |

## Decision
Relocate **`uqlab-flask/`** → **`src/flask_ui/`**.

### Rationale
- It is a root-level UI package, separate from the ML core (`src/uqlab_core/`) and orchestrator (`src/uqlab_orchestrator/`).
- Moving it under `src/` aligns with the package-reorganization principle that UI code should live in its own package rather than at the repository root.
- The move is contained: only `START_HERE.md` and `docs/UQLAB_FLOW.md` reference it externally.
- While relocating, we can also fix the broken `uqlab` imports to use `uqlab_core`, which is the canonical package today.

### New layout
```text
src/flask_ui/
├── app.py              # Flask app factory (was uqlab-flask/app.py)
├── executor.py         # Background sweep worker (was uqlab_flask/executor.py)
├── runs.py             # API routes (was uqlab_flask/routes/runs.py)
├── wizard.py           # 5-step wizard routes (was uqlab_flask/routes/wizard.py)
├── templates/          # HTML templates
├── static/             # CSS
├── README.md
└── requirements.txt
```

### Import changes
- `uqlab_flask.routes.runs` → `flask_ui.runs`
- `uqlab_flask.routes.wizard` → `flask_ui.wizard`
- `uqlab_flask.executor` → `flask_ui.executor`
- `uqlab.runner.execute` → `uqlab_core.runner.execute`
- `uqlab.evaluation.reporting.sweep_line_plot` → `uqlab_core.evaluation.reporting.sweep_line_plot`

### Files to update
- `uqlab-flask/app.py` → `src/flask_ui/app.py` (template/static paths + blueprint imports)
- `uqlab-flask/uqlab_flask/routes/runs.py` → `src/flask_ui/runs.py`
- `uqlab-flask/uqlab_flask/routes/wizard.py` → `src/flask_ui/wizard.py`
- `uqlab-flask/uqlab_flask/executor.py` → `src/flask_ui/executor.py`
- `START_HERE.md`
- `docs/UQLAB_FLOW.md`
- `src/flask_ui/README.md`
- `.gitignore` — added `!src/flask_ui/` so the new package is tracked

## Known issues carried over (not in scope)
The Flask wizard was already broken before the move because it referenced symbols that no longer exist in the current `uqlab_core` / `uqlab_orchestrator` packages:
- `uqlab_orchestrator.config.default_workflow` / `merge_workflow_defaults` are not present.
- `uqlab_core.evaluation.reporting.sweep_line_plot.build_sweep_line_plot` is not present.

These were updated to the new package names for consistency, but the underlying functionality will need separate restoration if the wizard is kept.

## Non-goals
- Do not touch `scripts/runners/` in this change; it is too entangled with the FastAPI backend and documentation.
- Do not delete the empty `src/uqlab/` workspace member yet; that is a separate cleanup task.
