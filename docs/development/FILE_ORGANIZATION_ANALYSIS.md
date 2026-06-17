# File Organization Analysis: api_sweep_launch.py

## Current Location (Wrong)
```
uqlab-streamlit/ui_components/api_sweep_launch.py
```

**Problem**: This file contains API orchestration logic, not UI components.

## What the File Does

### Core Responsibilities
1. **API Communication** - Makes HTTP requests to backend
2. **Experiment Creation** - Builds experiment payloads
3. **Sweep Orchestration** - Manages multi-experiment sweeps
4. **Batch Operations** - Creates multiple experiments at once

### Key Functions
- `create_and_start_one()` - Create single experiment via API
- `launch_api_sweep()` - Launch multiple experiments (sweep)
- `build_experiment_payload()` - Build API request payload
- `launch_paired_both_sweeps()` - Launch epistemic + aleatoric sweeps

### Dependencies
- `requests` - HTTP client
- `uqlab.validation_config` - Sweep configuration
- `ui_components.experiment_config` - Config builder (also misplaced!)

## Proposed Solutions

### Option 1: Move to `src/uqlab_orchestrator/` ✅ **RECOMMENDED**

**New Location**:
```
uqlab-streamlit/src/uqlab_orchestrator/api_client.py
```

**Rationale**:
- ✅ Already have `uqlab_orchestrator` package for orchestration
- ✅ Fits with `BatchGenerator`, `ExperimentRunner`
- ✅ Clear separation: orchestration vs UI
- ✅ Reusable across different UIs (Streamlit, CLI, notebooks)

**Structure**:
```
src/uqlab_orchestrator/
├── __init__.py
├── batch/
│   ├── generator.py          # BatchGenerator (existing)
│   └── orchestrator.py        # BatchOrchestrator (existing)
├── api_client.py              # ← Move api_sweep_launch.py here
└── experiment_runner.py       # ExperimentRunner (existing)
```

### Option 2: Create `src/uqlab/api/` Package

**New Location**:
```
uqlab-streamlit/src/uqlab/api/client.py
```

**Rationale**:
- ✅ Dedicated API client package
- ✅ Could add more API-related modules
- ✅ Clear purpose

**Structure**:
```
src/uqlab/api/
├── __init__.py
├── client.py                  # ← Move api_sweep_launch.py here
├── models.py                  # API request/response models
└── exceptions.py              # API-specific exceptions
```

### Option 3: Move to `backend/app/client/`

**New Location**:
```
uqlab-streamlit/backend/app/client/sweep_launcher.py
```

**Rationale**:
- ✅ Co-located with backend
- ✅ Clear it's a backend client
- ❌ But frontend shouldn't import from backend/

**Not recommended** - breaks frontend/backend separation.

## Recommended Refactoring

### Step 1: Move to `uqlab_orchestrator`

```bash
# Move file
mv uqlab-streamlit/ui_components/api_sweep_launch.py \
   uqlab-streamlit/src/uqlab_orchestrator/api_client.py
```

### Step 2: Rename and Refactor

**Before** (`ui_components/api_sweep_launch.py`):
```python
def launch_api_sweep(...):
    """Launch sweep via API."""
    ...
```

**After** (`uqlab_orchestrator/api_client.py`):
```python
class ExperimentAPIClient:
    """Client for experiment API operations."""
    
    def __init__(self, base_url: str, get_headers: Callable):
        self.base_url = base_url
        self.get_headers = get_headers
    
    def create_experiment(self, payload: Dict) -> Dict:
        """Create single experiment."""
        ...
    
    def start_experiment(self, exp_id: str) -> bool:
        """Start experiment."""
        ...
    
    def launch_sweep(
        self,
        workflow: Dict,
        sweep_axis: str,
        points: List[Tuple[int, float]],
        auto_start: bool = True
    ) -> Dict:
        """Launch multi-experiment sweep."""
        ...
```

### Step 3: Update Imports

**In `streamlit_app_progressive.py`**:
```python
# Before
from ui_components.api_sweep_launch import launch_api_sweep

# After
from uqlab_orchestrator.api_client import ExperimentAPIClient

# Usage
client = ExperimentAPIClient(API_BASE_URL, get_headers)
result = client.launch_sweep(workflow, "1d_epistemic", points)
```

### Step 4: Also Move `experiment_config.py`

**Current**: `ui_components/experiment_config.py`  
**Should be**: `uqlab_orchestrator/config_builder.py`

**Rationale**: Config building is orchestration logic, not UI.

## Final Structure

```
uqlab-streamlit/
├── src/
│   ├── uqlab/                          # ML/UQ logic
│   │   ├── classification/
│   │   ├── shared/
│   │   └── ui_components/              # ONLY UI rendering
│   │       ├── results.py              # ✅ UI component
│   │       ├── signal_visualization.py # ✅ UI component
│   │       └── validation_runner.py    # ✅ UI component
│   │
│   └── uqlab_orchestrator/             # Orchestration logic
│       ├── __init__.py
│       ├── api_client.py               # ← api_sweep_launch.py
│       ├── config_builder.py           # ← experiment_config.py
│       ├── batch/
│       │   ├── generator.py
│       │   └── orchestrator.py
│       └── experiment_runner.py
│
├── ui_components/                      # Streamlit-specific UI
│   ├── dataset_selection.py           # ✅ UI component
│   ├── model_selector.py              # ✅ UI component
│   ├── results.py                     # ✅ UI component
│   └── smart_experiment_selector.py   # ✅ UI component
│
└── streamlit_app_progressive.py
```

## Benefits of Reorganization

### 1. **Clear Separation of Concerns**
- UI components render UI
- Orchestrator handles execution
- API client handles communication

### 2. **Better Reusability**
```python
# Can use in Streamlit
from uqlab_orchestrator.api_client import ExperimentAPIClient
client = ExperimentAPIClient(...)

# Can use in CLI
from uqlab_orchestrator.api_client import ExperimentAPIClient
client = ExperimentAPIClient(...)

# Can use in Jupyter
from uqlab_orchestrator.api_client import ExperimentAPIClient
client = ExperimentAPIClient(...)
```

### 3. **Easier Testing**
```python
# Test API client without UI
def test_create_experiment():
    client = ExperimentAPIClient("http://test", lambda: {})
    result = client.create_experiment(payload)
    assert result["id"]
```

### 4. **Better Discoverability**
```python
# Clear what each package does
from uqlab import ...                    # ML/UQ algorithms
from uqlab_orchestrator import ...       # Execution orchestration
from ui_components import ...            # UI rendering
```

## Migration Script

```bash
#!/bin/bash
# migrate_api_client.sh

set -e

echo "🔄 Migrating api_sweep_launch.py to uqlab_orchestrator..."

# Create api_client.py in orchestrator
mv uqlab-streamlit/ui_components/api_sweep_launch.py \
   uqlab-streamlit/src/uqlab_orchestrator/api_client.py

# Update imports in progressive app
sed -i '' 's/from ui_components.api_sweep_launch/from uqlab_orchestrator.api_client/g' \
    uqlab-streamlit/streamlit_app_progressive.py

# Also move experiment_config.py
mv uqlab-streamlit/ui_components/experiment_config.py \
   uqlab-streamlit/src/uqlab_orchestrator/config_builder.py

# Update imports
sed -i '' 's/from ui_components.experiment_config/from uqlab_orchestrator.config_builder/g' \
    uqlab-streamlit/streamlit_app_progressive.py

echo "✅ Migration complete!"
echo ""
echo "Next steps:"
echo "1. Refactor api_client.py to use class-based API"
echo "2. Add unit tests"
echo "3. Update documentation"
```

## Summary

**Current**: `ui_components/api_sweep_launch.py` ❌  
**Recommended**: `src/uqlab_orchestrator/api_client.py` ✅

**Why**: API orchestration logic belongs in the orchestrator package, not UI components. This improves:
- ✅ Code organization
- ✅ Reusability
- ✅ Testability
- ✅ Discoverability
- ✅ Separation of concerns