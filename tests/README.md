# Test Suite

This directory contains unit and integration tests for the uqlab-streamlit uncertainty quantification project.

Tests are organized by domain into subfolders:

| Subfolder | Domain | Example files |
|-----------|--------|---------------|
| `config/` | Configuration validation and schema | `test_config_schema.py`, `test_workflow_validation.py` |
| `data/` | Data loading, sampling, and splits | `test_dataset_factory.py`, `test_four_region_split.py` |
| `models/` | Model architectures and training modes | `test_resnet_modes.py`, `test_resnet_training_modes.py` |
| `runner/` | Experiment runner, artifacts, and execution | `test_runner_pipeline.py`, `test_run_recovery.py` |
| `evaluation/` | Evaluation metrics, signals, and uncertainty | `test_evaluation.py`, `test_uncertainty_metrics.py` |
| `four_region/` | Four-region split and reporting | `test_four_region_validation.py` |
| `campaign/` | Campaign orchestration, scoring, and sweeps | `test_campaign_report.py`, `test_paper_benchmark_plot.py` |
| `visualization/` | Plots, UI, and exports | `test_plot_export.py`, `test_ui_import_is_light.py` |
| `smoke/` | Minimal sanity checks | `test_minimal.py` |
| `legacy/` | Legacy compatibility tests | (separate) |

## Running Tests

### Quick Start

```bash
# Install pytest (if not already installed)
pip install pytest

# Run all tests
pytest

# Run tests in a specific domain
pytest tests/config/

# Run a specific test file
pytest tests/config/test_config_schema.py

# Run with verbose output
pytest -v
```

### Test Categories

Tests are organized by markers:

```bash
# Run only fast unit tests
pytest -m unit

# Run integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Run GPU tests (requires GPU)
pytest -m gpu
```

### Coverage

```bash
# Install coverage tool
pip install pytest-cov

# Run with coverage report
pytest --cov=uqlab --cov=app --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=uqlab --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Writing Tests

### Test Structure

```python
import pytest
import torch

class TestFeatureName:
    """Tests for specific feature."""

    def test_basic_functionality(self):
        """Test basic use case."""
        result = function_under_test()
        assert result == expected_value

    @pytest.mark.slow
    def test_expensive_operation(self):
        """Test that takes time."""
        # Mark slow tests so they can be skipped
        pass
```

### Fixtures

Use `conftest.py` for shared fixtures:

```python
# conftest.py
import pytest

@pytest.fixture
def sample_config():
    """Provide sample configuration for tests."""
    return {...}
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive test names** - `test_auroc_perfect_separation` not `test_1`
3. **Use markers** - Mark slow/GPU/integration tests
4. **Test edge cases** - Empty inputs, invalid values, boundary conditions
5. **Keep tests fast** - Mock expensive operations
6. **Place tests by domain** - Add new tests to the relevant subfolder

## Continuous Integration

Tests can be integrated into CI/CD:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest -m "not slow and not gpu"
```
