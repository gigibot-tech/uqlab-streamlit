# uq_classification Consolidation

## What Changed

The `uq_classification` symlink has been removed. All code now uses the canonical path:

```python
# OLD (via symlink)
from uq_classification.models import EmbeddingDataset

# NEW (canonical path)
from uqlab.evaluation.classification.models import EmbeddingDataset
```

## Why

1. **Clarity**: The symlink created confusion about the actual code location
2. **Maintainability**: Single source of truth for imports
3. **SoC**: Clear separation between general (`uqlab/`) and classification-specific (`uqlab/evaluation/classification/`)

## Backup

A backup of the original `uqlab/evaluation/classification/` directory exists at:
- `src/uqlab_classification_backup/`

## Files Updated

All imports in the following files were updated:
- `scripts/run_fast_uncertainty_classification.py`
- `scripts/examples/minimal_experiment.py`
- `tests/test_evaluation.py`
- `tests/test_config_schema.py`
- `tests/legacy/test_model_config.py`
- `scripts/legacy/export_to_watsonx.py`
- `tests/legacy/test_refactor.py`
- `tests/legacy/test_model_config_simple.py`
- `streamlit_app.py`
- `src/uqlab/data/__init__.py`
- `src/uqlab/ui_components/results/results.py`
- `src/uqlab/ui_components/visualization/signals/signal_visualization.py`
- `src/uqlab/ui_components/visualization/signals/signal_diagnostic_viz.py`
- `backend/app/services/executors/direct_executor.py`

## Rollback

If needed, you can rollback by:
1. Restoring the symlink: `ln -s uqlab/evaluation/classification src/uq_classification`
2. Reverting the import changes: `git revert <commit-hash>`
