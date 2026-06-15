# Archive Directory

This directory contains experimental and example code that's not part of the core library.

## Structure

### `watsonx_experiments/`
WatsonX.ai integration experiments and scoring implementations:
- `watsonx_custom_scorer.py` - Custom scoring implementation
- `watsonx_dualxda_example.py` - DualXDA with WatsonX example
- `watsonx_export.py` - Model export utilities
- `watsonx_parameterized.py` - Parameterized experiments
- `watsonx_scoring.py` - Scoring implementation
- `watsonx_scoring copy.py` - Duplicate (can be deleted)
- `watsonx_uncertainty.py` - Uncertainty quantification with WatsonX

**Note**: The active WatsonX integration is in `../watsonx_streamlit.py` (parent directory)

### `examples_and_tests/`
Example scripts and integration tests:
- `example_decision_boundary.py` - Decision boundary visualization example
- `example_streamlit_workflow.py` - Streamlit workflow example
- `test_checkpoint_viz_integration.py` - Checkpoint visualization tests
- `test_merge.py` - Merge testing
- `train_with_checkpoints.py` - Training with checkpoint saving

**Note**: Unit tests are in `../../tests/` (project root)

## Why Archived?

These files were moved to keep the main `uq_classification/` directory focused on core functionality:
- Core modules: `data_loader.py`, `evaluation.py`, `models.py`, etc.
- Active integrations: `watsonx_streamlit.py`, `config_schema.py`
- Utilities: `utils.py`, `unified_tracker.py`

## Usage

Files in this archive can still be imported if needed:
```python
from uq_classification.archive.watsonx_experiments import watsonx_scoring
```

Or run directly:
```bash
python -m uq_classification.archive.examples_and_tests.example_decision_boundary
```

## Made with Bob