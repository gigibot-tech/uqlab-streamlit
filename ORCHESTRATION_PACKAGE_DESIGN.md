# Orchestration Package Design

## Overview

Create a dedicated `uqlab_orchestrator` package that manages:
1. **Experiment Execution** - Running scripts with configs
2. **Batch Management** - Generating and tracking sweep experiments
3. **Sweep Coordination** - 1D/2D sweep detection and execution
4. **Result Collection** - Gathering and organizing results

## Package Structure

```
src/
├── uqlab/                    # Core ML package (1_data → 4_evaluation)
│   ├── 1_data/
│   ├── 2_models/
│   ├── 3_training/
│   ├── 4_evaluation/
│   └── ...
│
└── uqlab_orchestrator/       # NEW: Orchestration package
    ├── __init__.py
    ├── config/               # Config management
    │   ├── __init__.py
    │   ├── validator.py      # Validate ExperimentConfig
    │   └── serializer.py     # Save/load configs
    │
    ├── execution/            # Script execution
    │   ├── __init__.py
    │   ├── runner.py         # ExperimentRunner class
    │   └── script_mapper.py  # Map config → script path
    │
    ├── batch/                # Batch experiment management
    │   ├── __init__.py
    │   ├── generator.py      # BatchGenerator class
    │   ├── sweep_detector.py # Detect 1D/2D sweeps
    │   └── tracker.py        # Track batch progress
    │
    ├── sweeps/               # Sweep-specific logic
    │   ├── __init__.py
    │   ├── epistemic.py      # 1D epistemic sweeps
    │   ├── aleatoric.py      # 1D aleatoric sweeps
    │   └── grid_2d.py        # 2D grid sweeps
    │
    └── results/              # Result management
        ├── __init__.py
        ├── collector.py      # Collect results from disk
        └── aggregator.py     # Aggregate batch results
```

## Core Classes

### 1. ExperimentRunner

**Purpose**: Execute a single experiment with a config

```python
# src/uqlab_orchestrator/execution/runner.py
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
import json
from backend.app.domain.models import ExperimentConfig

class ExperimentRunner:
    """Executes experiments by calling the appropriate script with config."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.scripts_dir = workspace_root / "scripts"
    
    def run(
        self,
        config: ExperimentConfig,
        experiment_id: str,
        script_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run an experiment.
        
        Args:
            config: Experiment configuration
            experiment_id: Unique experiment ID
            script_name: Optional script override (default: auto-detect)
        
        Returns:
            Result dictionary with paths and metrics
        """
        # 1. Determine which script to run
        script_path = self._get_script_path(config, script_name)
        
        # 2. Save config to temp file
        config_path = self._save_config(config, experiment_id)
        
        # 3. Execute script
        result = subprocess.run(
            ["python", str(script_path), "--config", str(config_path)],
            capture_output=True,
            text=True,
            cwd=self.workspace_root
        )
        
        # 4. Load results
        results_dir = Path(config.paths.results_base_dir) / experiment_id
        return self._load_results(results_dir, result)
    
    def _get_script_path(
        self,
        config: ExperimentConfig,
        override: Optional[str]
    ) -> Path:
        """Map config to appropriate script."""
        if override:
            return self.scripts_dir / override
        
        # Auto-detect based on config
        if config.model.architecture.startswith("dinov2"):
            return self.scripts_dir / "run_fast_uncertainty_classification.py"
        elif config.model.architecture.startswith("resnet"):
            return self.scripts_dir / "run_fast_uncertainty_classification.py"
        else:
            raise ValueError(f"Unknown architecture: {config.model.architecture}")
    
    def _save_config(self, config: ExperimentConfig, exp_id: str) -> Path:
        """Save config to temp file."""
        config_dir = self.workspace_root / "temp_configs"
        config_dir.mkdir(exist_ok=True)
        
        config_path = config_dir / f"{exp_id}.json"
        config_path.write_text(json.dumps(config.model_dump(), indent=2))
        return config_path
    
    def _load_results(self, results_dir: Path, process_result) -> Dict[str, Any]:
        """Load results from disk."""
        if not results_dir.exists():
            return {
                "status": "failed",
                "error": process_result.stderr,
                "stdout": process_result.stdout
            }
        
        # Load summary.json if exists
        summary_path = results_dir / "summary.json"
        if summary_path.exists():
            return json.loads(summary_path.read_text())
        
        return {
            "status": "completed",
            "results_dir": str(results_dir),
            "stdout": process_result.stdout
        }
```

### 2. BatchGenerator

**Purpose**: Generate multiple configs for sweep experiments

```python
# src/uqlab_orchestrator/batch/generator.py
from typing import List, Dict, Any
from backend.app.domain.models import ExperimentConfig, DataConfig, EvaluationConfig

class SweepType:
    """Sweep type enumeration."""
    EPISTEMIC_1D = "epistemic_1d"
    ALEATORIC_1D = "aleatoric_1d"
    GRID_2D = "grid_2d"
    SINGLE_POINT = "single_point"

class BatchGenerator:
    """Generates experiment configs for batch sweeps."""
    
    def generate_epistemic_sweep(
        self,
        base_config: ExperimentConfig,
        under_train_values: List[int]
    ) -> List[ExperimentConfig]:
        """
        Generate 1D epistemic sweep (vary dataset size).
        
        Args:
            base_config: Base configuration
            under_train_values: List of under_train_per_class values
        
        Returns:
            List of configs, one per sweep point
        """
        configs = []
        for under_train in under_train_values:
            # Deep copy and modify
            config = base_config.model_copy(deep=True)
            config.data.under_train_per_class = under_train
            configs.append(config)
        return configs
    
    def generate_aleatoric_sweep(
        self,
        base_config: ExperimentConfig,
        noise_values: List[float]
    ) -> List[ExperimentConfig]:
        """
        Generate 1D aleatoric sweep (vary label noise).
        
        Args:
            base_config: Base configuration
            noise_values: List of noise percentages (0-100)
        
        Returns:
            List of configs, one per sweep point
        """
        configs = []
        for noise in noise_values:
            config = base_config.model_copy(deep=True)
            config.data.aleatoric_noise_percentage = noise
            configs.append(config)
        return configs
    
    def generate_2d_grid(
        self,
        base_config: ExperimentConfig,
        under_train_values: List[int],
        noise_values: List[float]
    ) -> List[ExperimentConfig]:
        """
        Generate 2D grid sweep (vary both dimensions).
        
        Args:
            base_config: Base configuration
            under_train_values: List of dataset sizes
            noise_values: List of noise percentages
        
        Returns:
            List of configs for full grid (len = len(under) × len(noise))
        """
        configs = []
        for under_train in under_train_values:
            for noise in noise_values:
                config = base_config.model_copy(deep=True)
                config.data.under_train_per_class = under_train
                config.data.aleatoric_noise_percentage = noise
                configs.append(config)
        return configs
    
    def detect_sweep_type(
        self,
        configs: List[ExperimentConfig]
    ) -> SweepType:
        """
        Detect sweep type from list of configs.
        
        Returns:
            SweepType enum value
        """
        if len(configs) == 1:
            return SweepType.SINGLE_POINT
        
        # Check which parameters vary
        under_train_values = set(c.data.under_train_per_class for c in configs)
        noise_values = set(c.data.aleatoric_noise_percentage for c in configs)
        
        varies_under = len(under_train_values) > 1
        varies_noise = len(noise_values) > 1
        
        if varies_under and varies_noise:
            return SweepType.GRID_2D
        elif varies_under:
            return SweepType.EPISTEMIC_1D
        elif varies_noise:
            return SweepType.ALEATORIC_1D
        else:
            return SweepType.SINGLE_POINT
```

### 3. BatchOrchestrator

**Purpose**: Coordinate batch execution

```python
# src/uqlab_orchestrator/batch/orchestrator.py
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from backend.app.domain.models import ExperimentConfig
from .generator import BatchGenerator, SweepType
from ..execution.runner import ExperimentRunner

class BatchOrchestrator:
    """Orchestrates batch experiment execution."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.runner = ExperimentRunner(workspace_root)
        self.generator = BatchGenerator()
    
    def execute_batch(
        self,
        batch_name: str,
        configs: List[ExperimentConfig],
        auto_start: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a batch of experiments.
        
        Args:
            batch_name: Name for this batch
            configs: List of experiment configs
            auto_start: Whether to start immediately
        
        Returns:
            Batch execution summary
        """
        # 1. Detect sweep type
        sweep_type = self.generator.detect_sweep_type(configs)
        
        # 2. Create batch metadata
        batch_id = f"{batch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        batch_dir = self.workspace_root / "batches" / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        metadata = {
            "batch_id": batch_id,
            "batch_name": batch_name,
            "sweep_type": sweep_type,
            "total_experiments": len(configs),
            "created_at": datetime.now().isoformat(),
            "status": "pending" if not auto_start else "running"
        }
        
        # Save metadata
        (batch_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
        
        # 3. Execute experiments if auto_start
        results = []
        if auto_start:
            for i, config in enumerate(configs):
                exp_id = f"{batch_id}_exp_{i:03d}"
                try:
                    result = self.runner.run(config, exp_id)
                    results.append({
                        "experiment_id": exp_id,
                        "status": "completed",
                        "result": result
                    })
                except Exception as e:
                    results.append({
                        "experiment_id": exp_id,
                        "status": "failed",
                        "error": str(e)
                    })
        
        # 4. Save results
        (batch_dir / "results.json").write_text(json.dumps(results, indent=2))
        
        return {
            "batch_id": batch_id,
            "sweep_type": sweep_type,
            "total": len(configs),
            "completed": len([r for r in results if r["status"] == "completed"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
```

## Integration with Streamlit

### Progressive App Integration

```python
# streamlit_app_progressive.py
from uqlab_orchestrator import BatchOrchestrator, BatchGenerator
from backend.app.domain.models import ExperimentConfig

def _launch_workflow_experiments(workflow, auto_start):
    """Launch batch experiments using orchestrator."""
    
    # 1. Build base config
    base_config = ExperimentConfig(
        seed=42,
        device="auto",
        data=DataConfig(...),
        model=ModelConfig(...),
        training=TrainingRuntimeConfig(...),
        evaluation=EvaluationConfig(...),
        paths=PathsConfig(...)
    )
    
    # 2. Generate sweep configs
    generator = BatchGenerator()
    
    if sweep_mode == "epistemic":
        configs = generator.generate_epistemic_sweep(
            base_config,
            under_train_values=[25, 50, 100, 200]
        )
    elif sweep_mode == "aleatoric":
        configs = generator.generate_aleatoric_sweep(
            base_config,
            noise_values=[0, 25, 50, 75, 100]
        )
    else:  # 2D grid
        configs = generator.generate_2d_grid(
            base_config,
            under_train_values=[50, 100, 200],
            noise_values=[0, 25, 50, 75]
        )
    
    # 3. Execute batch
    orchestrator = BatchOrchestrator(Path.cwd())
    result = orchestrator.execute_batch(
        batch_name=f"sweep_{timestamp}",
        configs=configs,
        auto_start=auto_start
    )
    
    return result
```

## Benefits

### ✅ Separation of Concerns
- **uqlab**: ML logic (data, models, training, evaluation)
- **uqlab_orchestrator**: Execution logic (running, batching, sweeping)
- **UI**: User interface (Streamlit apps)

### ✅ Clear Responsibilities
```
┌─────────────────────────────────────────┐
│ Streamlit UI                            │
│ - Collect user input                    │
│ - Build ExperimentConfig                │
│ - Display results                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ uqlab_orchestrator                      │
│ - Generate batch configs                │
│ - Detect sweep type (1D/2D)             │
│ - Execute scripts                       │
│ - Collect results                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ scripts/run_fast_*.py                   │
│ - Load config                           │
│ - Use uqlab package (1→2→3→4)           │
│ - Save results                          │
└─────────────────────────────────────────┘
```

### ✅ Testable
Each component can be tested independently:
```python
# Test batch generation
generator = BatchGenerator()
configs = generator.generate_epistemic_sweep(base, [50, 100])
assert len(configs) == 2
assert configs[0].data.under_train_per_class == 50

# Test sweep detection
sweep_type = generator.detect_sweep_type(configs)
assert sweep_type == SweepType.EPISTEMIC_1D

# Test execution (mock)
runner = ExperimentRunner(Path.cwd())
result = runner.run(config, "test_exp_001")
assert result["status"] == "completed"
```

## Implementation Plan

1. **Create package structure**
   ```bash
   mkdir -p src/uqlab_orchestrator/{config,execution,batch,sweeps,results}
   touch src/uqlab_orchestrator/__init__.py
   ```

2. **Implement core classes**
   - ExperimentRunner
   - BatchGenerator
   - BatchOrchestrator

3. **Update Streamlit apps**
   - Replace manual batch logic with orchestrator
   - Use BatchGenerator for sweep creation

4. **Add tests**
   - Unit tests for each class
   - Integration tests for full workflow

5. **Update documentation**
   - API reference
   - Usage examples

This creates a **clean, maintainable architecture** where each package has a single, clear responsibility!