# Model-scope consolidation

## Trigger

`src/uqlab_core/models/scope/` was a small folder (3 files, ~180 LoC) sitting one level below `uqlab_core.models`. Each file was under 100 LoC, so it added nesting without adding organizational value.

## Decision

Flatten `scope/` into `uqlab_core.models/`:

- `src/uqlab_core/models/scope/architecture.py` -> `src/uqlab_core/models/architecture.py`
- `src/uqlab_core/models/scope/training_scope.py` -> `src/uqlab_core/models/training_scope.py`
- Remove the now-empty `scope/` package.

## Rationale

- The folder only contained architecture aliases and training-scope resolution.
- Both concepts are tightly coupled to model construction and runner execution.
- A flat `models/` package keeps related helpers next to `factory`, `features`, and `training`.
- Follows the same consolidation principle used elsewhere: folders with only 1-4 small files should be merged into a parent with a clear purpose.

## Import updates

All internal `uqlab_core.models.scope.*` imports were rewritten to the new top-level module paths, including:

- `src/uqlab_core/models/__init__.py` lazy import map
- `src/uqlab_core/models/factory/factory.py`
- `src/uqlab_core/models/features/feature_extractors.py`
- `src/uqlab_core/models/training_scope.py`
- `src/uqlab_core/runner/execute.py`
- `src/uqlab_core/shared/config/classification.py`
- `src/uqlab_core/data/buildData.py`
- `src/uqlab_core/data/splits/experiment_loader.py`

## Verification

- `grep -R "uqlab_core.models.scope"` returns no matches.
- All modified files pass `python3 -m py_compile`.
