# Test Suite

This directory contains unit and integration tests for the uqlab-streamlit uncertainty quantification project.

## Running Tests

### Quick Start

```bash
# Install pytest (if not already installed)
pip install pytest

# Run all tests
pytest

# Run specific test file
pytest tests/test_config_schema.py

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
pytest --cov=uq_classification --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=uq_classification --cov-report=html
# Open htmlcov/index.html in browser
```

## Test Files

- `test_config_schema.py` - Configuration validation tests
- `test_evaluation.py` - Evaluation metrics tests (AUROC, F1, etc.)
- `test_data_loader.py` - Data loading and sampling tests (to be added)
- `test_models.py` - Model architecture tests (to be added)

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

## Made with Bob