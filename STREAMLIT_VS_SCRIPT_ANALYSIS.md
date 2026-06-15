# Streamlit App vs run_fast_uncertainty_classification.py Analysis

## Your Question
> "everything before the run_fast script is just config creation for that file in the streamlit progressive app right? or not? if not tell me what else, and cant we make it more concise technically and SE best practice"

## Answer: NO, They Are Different Execution Paths

### Streamlit App (`streamlit_app_progressive.py`)
**Purpose**: Web UI for creating experiments via FastAPI backend

**Flow**:
1. User configures experiment in UI (Steps 1-4)
2. Streamlit builds JSON payload via `_build_experiment_payload()`
3. Sends HTTP POST to FastAPI backend: `/api/v1/experiments/no-auth`
4. Backend stores experiment in database
5. Backend calls training orchestrator (which may use the script internally)
6. Results displayed in UI from database

**Key Point**: This is a **client** that talks to the backend API.

### Script (`run_fast_uncertainty_classification.py`)
**Purpose**: Standalone CLI tool for running experiments directly

**Flow**:
1. Parse command-line arguments
2. Load data directly from disk
3. Train model in-process
4. Compute uncertainty metrics
5. Save results to disk (JSON/CSV)

**Key Point**: This is a **standalone executor** that bypasses the API.

## What Streamlit Actually Does

### NOT Just Config Creation
The Streamlit app does MORE than config:

1. **API Client** (lines 312-358):
   - Creates experiments via REST API
   - Starts training via API
   - Polls for results
   - Handles errors

2. **Results Visualization** (lines 415-448):
   - Fetches experiments from database
   - Renders tables, plots, metrics
   - Auto-refresh for live updates
   - Smart experiment selector

3. **Workflow Management** (lines 361-412):
   - Sweep planning (1D epistemic, 1D aleatoric, 2D grid)
   - Batch creation (multiple experiments at once)
   - Progress tracking
   - Error handling

4. **UI State Management** (lines 189-202):
   - Session state for multi-step workflow
   - Progressive disclosure (MLflow pattern)
   - Highlight newly created experiments

## Architecture Comparison

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT APP                             │
│  ┌──────────────┐    HTTP POST    ┌──────────────────────┐ │
│  │ UI Config    │ ──────────────> │ FastAPI Backend      │ │
│  │ (Steps 1-4)  │                 │ - Stores in DB       │ │
│  └──────────────┘                 │ - Calls orchestrator │ │
│         │                          └──────────────────────┘ │
│         │                                    │               │
│         │                                    ▼               │
│         │                          ┌──────────────────────┐ │
│         │                          │ Training Orchestrator│ │
│         │                          │ (may use script)     │ │
│         │                          └──────────────────────┘ │
│         │                                    │               │
│         ▼                                    ▼               │
│  ┌──────────────┐    HTTP GET     ┌──────────────────────┐ │
│  │ Results View │ <────────────── │ Database (results)   │ │
│  └──────────────┘                 └──────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    CLI SCRIPT                                │
│  ┌──────────────┐                                           │
│  │ CLI Args     │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │ Load Data    │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │ Train Model  │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐                                           │
│  │ Save Results │ ──> Disk (JSON/CSV)                      │
│  └──────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

## Can We Make It More Concise? YES!

### Current Issues (Anti-Patterns)

1. **Duplicate Config Logic** (lines 68-118, 252-295):
   - `DEFAULT_WORKFLOW` dict hardcoded
   - `_build_experiment_payload()` rebuilds same structure
   - Should use shared config schema

2. **Tight Coupling** (lines 312-358):
   - `_create_and_start_one()` knows too much about API structure
   - Should use API client class

3. **Mixed Concerns** (lines 361-412):
   - `_launch_workflow_experiments()` does:
     - Sweep planning
     - HTTP requests
     - Error handling
     - State management
   - Should be 4 separate functions

4. **No Validation** (lines 252-295):
   - `_build_experiment_payload()` doesn't validate config
   - Should use Pydantic models

### Refactoring Recommendations

#### 1. Extract API Client
```python
# ui_components/api_client.py
class ExperimentAPIClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    def create_experiment(self, config: ExperimentConfig) -> Experiment:
        """Create experiment from validated config"""
        response = requests.post(
            f"{self.base_url}/api/v1/experiments/no-auth",
            json=config.model_dump(),
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return Experiment(**response.json())
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start training for experiment"""
        response = requests.post(
            f"{self.base_url}/api/v1/experiments/no-auth/{experiment_id}/start",
            headers=self.headers,
            timeout=30
        )
        response.raise_for_status()
        return True
```

#### 2. Use Shared Config Schema
```python
# uqlab/shared/config/experiment_schema.py
from pydantic import BaseModel, Field

class DatasetConfig(BaseModel):
    dataset_name: str = "cifar10"
    noise_type: str = "clean_label"
    
class TrainingConfig(BaseModel):
    model_architecture: str = "dinov2-small"
    hidden_dim: int = 256
    dropout: float = 0.2
    epochs: int = 12
    learning_rate: float = 0.001
    batch_size: int = 256

class UncertaintyConfig(BaseModel):
    under_supported: str = "random:2"
    under_train_per_class: int = 50
    regular_train_per_class: int = 300
    custom_noise_rate: Optional[float] = None

class ExperimentConfig(BaseModel):
    name: str
    dataset: DatasetConfig
    training: TrainingConfig
    uncertainty: UncertaintyConfig
    evaluation: EvaluationConfig
```

#### 3. Separate Sweep Planning
```python
# ui_components/sweep_planner.py
class SweepPlanner:
    @staticmethod
    def plan_1d_aleatoric(
        base_config: ExperimentConfig,
        noise_values: List[float]
    ) -> List[ExperimentConfig]:
        """Generate configs for aleatoric sweep"""
        return [
            base_config.model_copy(
                update={"uncertainty": {"custom_noise_rate": noise}}
            )
            for noise in noise_values
        ]
    
    @staticmethod
    def plan_1d_epistemic(
        base_config: ExperimentConfig,
        dataset_sizes: List[int]
    ) -> List[ExperimentConfig]:
        """Generate configs for epistemic sweep"""
        return [
            base_config.model_copy(
                update={"uncertainty": {"under_train_per_class": size}}
            )
            for size in dataset_sizes
        ]
```

#### 4. Simplified Streamlit Code
```python
# streamlit_app_progressive.py (refactored)
def main():
    st.title("🔬 UQ Experiment Builder")
    
    # Initialize
    api_client = ExperimentAPIClient(API_BASE_URL, API_TOKEN)
    planner = SweepPlanner()
    
    # Step 1-4: Build config (using Pydantic forms)
    config = build_experiment_config_ui()
    
    # Step 5: Launch
    if st.button("Launch Sweep"):
        # Plan sweep
        configs = planner.plan_1d_aleatoric(
            config,
            noise_values=[0, 25, 50, 75, 100]
        )
        
        # Create & start experiments
        experiments = []
        for cfg in configs:
            exp = api_client.create_experiment(cfg)
            api_client.start_experiment(exp.id)
            experiments.append(exp)
        
        st.success(f"Launched {len(experiments)} experiments")
    
    # Results
    render_experiment_results(api_client)
```

### Benefits of Refactoring

1. **Separation of Concerns**:
   - API client handles HTTP
   - Planner handles sweep logic
   - UI handles rendering

2. **Testability**:
   - Can mock API client
   - Can test planner independently
   - Can test UI components in isolation

3. **Reusability**:
   - API client usable from CLI
   - Planner usable in notebooks
   - Config schema shared everywhere

4. **Type Safety**:
   - Pydantic validates all configs
   - IDE autocomplete works
   - Catch errors at config time, not runtime

5. **Maintainability**:
   - 400 lines → ~150 lines
   - Clear responsibilities
   - Easy to extend

## Conclusion

**Current State**: Streamlit app is NOT just config creation - it's a full API client with visualization, state management, and workflow orchestration.

**Problem**: Mixed concerns, duplicate logic, no validation, tight coupling.

**Solution**: Extract API client, use shared Pydantic schemas, separate sweep planning, simplify UI code.

**Impact**: 60% code reduction, better testability, easier maintenance, type safety.