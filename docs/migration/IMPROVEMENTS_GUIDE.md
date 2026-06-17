# Code Quality Improvements Guide

This document describes the optional code quality improvements added to the uqlab-streamlit project. All improvements are **backward compatible** and **optional** - the existing code continues to work without any changes.

## Overview

Three main improvements have been added:

1. **Configuration Validation** - Type-safe config with validation
2. **Unit Tests** - Test suite for core functionality
3. **Type Checking** - Optional mypy support for better IDE experience

## 1. Configuration Validation

### What Was Added

A new module `uq_classification/config_schema.py` provides dataclass-based configuration with validation.

### Benefits

- **Type safety**: Catch configuration errors before running experiments
- **Validation**: Automatic validation of parameter ranges and formats
- **IDE support**: Better autocomplete and error detection
- **Documentation**: Self-documenting configuration structure

### Usage

#### Option A: New Way (With Validation)

```python
from uq_classification.config_schema import ExperimentConfig

# Load from YAML with validation
config = ExperimentConfig.from_yaml("config.yaml")
config.validate()  # Raises ValueError if invalid

# Access with type safety
print(config.data.noise_type)  # IDE knows this is a string
print(config.model.hidden_dim)  # IDE knows this is an int
```

#### Option B: Old Way (Still Works!)

```python
import yaml

# Your existing code continues to work
with open("config.yaml") as f:
    config_dict = yaml.safe_load(f)

# Use config_dict as before - no changes needed
```

#### Option C: Validate Existing Dict

```python
from uq_classification.config_schema import validate_config_dict

# Validate your existing dict without converting
config_dict = {...}
validate_config_dict(config_dict)  # Raises if invalid
# Continue using config_dict as before
```

### Configuration Structure

```python
@dataclass
class ExperimentConfig:
    seed: int = 42
    device: str = "auto"
    data: DataConfig          # Data sampling parameters
    model: ModelConfig        # Model architecture
    training: TrainingConfig  # Training hyperparameters
    evaluation: EvaluationConfig  # Evaluation settings
    paths: PathsConfig        # File paths
```

### Validation Examples

```python
# Invalid noise type
config = DataConfig(noise_type="invalid")
config.validate()  # Raises: Invalid noise_type

# Invalid class range
config = DataConfig(under_supported_classes="0,15")
config.validate()  # Raises: Class IDs must be between 0 and 9

# Invalid dropout
config = ModelConfig(dropout=1.5)
config.validate()  # Raises: dropout must be in [0, 1)
```

## 2. Unit Tests

### What Was Added

A test suite in `tests/` directory with pytest configuration.

### Structure

```
tests/
├── __init__.py
├── test_config_schema.py   # Configuration validation tests
├── test_evaluation.py      # Evaluation metrics tests
└── conftest.py            # Shared fixtures (to be added)
```

### Running Tests

```bash
# Install pytest (optional)
pip install pytest pytest-cov

# Run all tests
pytest

# Run specific test file
pytest tests/test_config_schema.py

# Run with coverage
pytest --cov=uq_classification --cov-report=html

# Run only fast unit tests
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

### Test Categories

Tests are marked with categories:

- `@pytest.mark.unit` - Fast unit tests (no external dependencies)
- `@pytest.mark.integration` - Integration tests (may require data files)
- `@pytest.mark.slow` - Slow tests (feature extraction, training)
- `@pytest.mark.gpu` - Tests requiring GPU
- `@pytest.mark.optional` - Tests for optional features

### Example Test

```python
def test_binary_auroc_perfect_separation():
    """Test AUROC with perfect separation."""
    scores = torch.tensor([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    positives = torch.tensor([False, False, False, True, True, True])
    
    auroc = binary_auroc(scores, positives)
    assert auroc == 1.0
```

## 3. Type Checking (mypy)

### What Was Added

A `mypy.ini` configuration file for optional static type checking.

### Benefits

- **Early error detection**: Catch type errors before runtime
- **Better IDE support**: Improved autocomplete and inline documentation
- **Code documentation**: Type hints serve as inline documentation
- **Refactoring safety**: Catch breaking changes during refactoring

### Usage

```bash
# Install mypy (optional)
pip install mypy

# Check entire project
mypy .

# Check specific module
mypy uq_classification/config_schema.py

# Check with strict settings
mypy --strict uq_classification/config_schema.py
```

### Configuration

The `mypy.ini` file is configured for **gradual typing**:

- Lenient by default (won't break existing code)
- Strict checking for new modules (like `config_schema.py`)
- Ignores missing imports for third-party libraries
- Can be made stricter over time

### Example Type Hints

```python
# Before (still works)
def binary_auroc(scores, positives):
    ...

# After (better IDE support)
def binary_auroc(scores: torch.Tensor, positives: torch.Tensor) -> float:
    ...
```

## Installation

### Minimal (No Changes Required)

Your existing code works without any changes. No installation needed.

### Optional Testing

```bash
pip install pytest pytest-cov
pytest  # Run tests
```

### Optional Type Checking

```bash
pip install mypy
mypy .  # Check types
```

### Full Development Setup

```bash
# Install all optional development tools
pip install pytest pytest-cov mypy black ruff

# Run tests
pytest

# Check types
mypy .

# Format code (optional)
black .

# Lint code (optional)
ruff check .
```

## Migration Guide

### For Existing Code

**No migration needed!** Your existing code continues to work:

```python
# This still works exactly as before
config_dict = yaml.safe_load(open("config.yaml"))
# Use config_dict as you always have
```

### For New Code

Consider using the new features:

```python
# New code can benefit from validation
from uq_classification.config_schema import ExperimentConfig

config = ExperimentConfig.from_yaml("config.yaml")
config.validate()  # Catch errors early
```

## Best Practices

### 1. Configuration

- **Use validation for new experiments**: Catch errors early
- **Keep dict-based code**: No need to change working code
- **Validate before long runs**: `validate_config_dict(config)` before training

### 2. Testing

- **Run tests before commits**: `pytest -m unit` (fast tests only)
- **Add tests for new features**: Follow existing test patterns
- **Use markers**: Mark slow tests with `@pytest.mark.slow`

### 3. Type Hints

- **Add hints to new code**: Helps IDE and documentation
- **Don't change working code**: Only add hints when refactoring
- **Use mypy optionally**: Not required for code to work

## Troubleshooting

### "pytest not found"

```bash
pip install pytest
```

Tests are optional - code works without pytest.

### "mypy not found"

```bash
pip install mypy
```

Type checking is optional - code works without mypy.

### "Import errors in tests"

Tests import from `uq_classification` package. Make sure you're running from project root:

```bash
cd uqlab-streamlit
pytest
```

### "Config validation too strict"

You can:
1. Use dict-based configs (no validation)
2. Use `validate_config_dict()` only when needed
3. Adjust validation rules in `config_schema.py`

## Summary

| Feature | Required? | Benefits | Installation |
|---------|-----------|----------|--------------|
| Config Validation | No | Type safety, early error detection | None (built-in) |
| Unit Tests | No | Reliability, regression prevention | `pip install pytest` |
| Type Checking | No | IDE support, documentation | `pip install mypy` |

**All improvements are optional and backward compatible!**

## Examples

### Example 1: Validate Before Long Training Run

```python
from uq_classification.config_schema import validate_config_dict

# Your existing config loading
config_dict = yaml.safe_load(open("config.yaml"))

# Add one line to catch errors early
validate_config_dict(config_dict)  # Raises if invalid

# Continue as before
run_experiment(config_dict)
```

### Example 2: Type-Safe Config Access

```python
from uq_classification.config_schema import ExperimentConfig

# Load with validation
config = ExperimentConfig.from_yaml("config.yaml")
config.validate()

# IDE knows types - better autocomplete!
noise_type: str = config.data.noise_type
hidden_dim: int = config.model.hidden_dim
```

### Example 3: Run Tests Before Commit

```bash
# Quick check (unit tests only, ~1 second)
pytest -m unit

# Full check (all tests, may take longer)
pytest

# With coverage report
pytest --cov=uq_classification --cov-report=term-missing
```

## Made with Bob