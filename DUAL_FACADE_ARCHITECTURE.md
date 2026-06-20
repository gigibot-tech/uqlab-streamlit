# 🏗️ Dual Facade Architecture: ML Core + Backend Integration

## 🎯 Problem Statement

**Question:** Should the backend/Streamlit use:
1. The same `ExperimentFacade` as the ML script?
2. A different facade with database capabilities?
3. A parent/superclass relationship?

**Answer:** **Option 2 + 3** - Use **Adapter Pattern** with **inheritance** for clean separation.

---

## 📐 Proposed Architecture

### Two Facades, Clear Responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI                              │
│  streamlit_app_progressive.py                                │
│                                                              │
│  User clicks "Run Experiment"                                │
│  ↓                                                           │
│  POST /api/v1/experiments                                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FASTAPI BACKEND                            │
│  backend/app/api/routes/experiments.py                       │
│                                                              │
│  create_experiment(config):                                  │
│    facade = BackendExperimentFacade(config, db_session)      │
│    result = await facade.run_and_persist()                   │
│    return result                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│            BackendExperimentFacade (NEW)                     │
│  backend/app/services/backend_experiment_facade.py           │
│                                                              │
│  Extends: ExperimentFacade                                   │
│  Adds: Database persistence, progress tracking, async       │
│                                                              │
│  async def run_and_persist(self):                            │
│    # 1. Create DB record                                     │
│    experiment = self._create_db_record()                     │
│                                                              │
│    # 2. Run ML experiment (inherited from parent)            │
│    result = await self._run_ml_experiment()                  │
│                                                              │
│    # 3. Persist results to DB                                │
│    self._save_to_database(experiment, result)                │
│                                                              │
│    return result                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (inherits from)
┌─────────────────────────────────────────────────────────────┐
│              ExperimentFacade (BASE)                         │
│  src/uqlab/orchestration/experiment_facade.py                │
│                                                              │
│  Pure ML logic, no database, no async                        │
│                                                              │
│  def run_experiment(self) -> ExperimentResult:               │
│    dataset = self.data_coordinator.prepare_dataset()         │
│    splits = self.data_coordinator.create_splits(dataset)     │
│    model = self.training_coordinator.train_model(splits)     │
│    signals = self.eval_coordinator.compute_signals(model)    │
│    return ExperimentResult(...)                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ (used by)
┌─────────────────────────────────────────────────────────────┐
│              CLI Script (Direct Usage)                       │
│  scripts/run_fast_uncertainty_classification.py              │
│                                                              │
│  def main():                                                 │
│    config = ExperimentConfig.from_yaml(args.config)          │
│    facade = ExperimentFacade(config)  # ← Base facade        │
│    result = facade.run_experiment()                          │
│    facade.save_results(result)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 💻 Implementation

### 1. Base Facade (ML Core - No Database)

**File:** `src/uqlab/orchestration/experiment_facade.py`

```python
"""
Base facade for ML experiments.

Pure ML logic:
- No database dependencies
- No async operations
- No progress callbacks
- Can be used standalone from CLI

Pattern: Facade (Gang of Four)
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from uqlab.shared.types import ExperimentConfig
from uqlab.orchestration.coordinators import (
    DataCoordinator,
    TrainingCoordinator,
    EvaluationCoordinator,
    ResultsCoordinator,
)


@dataclass
class ExperimentResult:
    """Pure ML experiment results (no database fields)"""
    auroc_scores: dict
    eval_sizes: dict
    signal_table: dict
    model_checkpoint: Path
    summary_path: Optional[Path] = None


class ExperimentFacade:
    """
    Base facade for ML experiments.
    
    Use this directly for:
    - CLI scripts
    - Jupyter notebooks
    - Standalone experiments
    - Testing
    
    Extend this for:
    - Backend integration (BackendExperimentFacade)
    - Custom workflows
    """
    
    def __init__(self, config: ExperimentConfig):
        """Initialize with ML config only"""
        self.config = config
        
        # Initialize coordinators
        self.data_coordinator = DataCoordinator(
            config.data, 
            config.paths
        )
        self.training_coordinator = TrainingCoordinator(
            config.model,
            config.training
        )
        self.evaluation_coordinator = EvaluationCoordinator(
            config.evaluation
        )
        self.results_coordinator = ResultsCoordinator(
            config.paths
        )
    
    def run_experiment(self) -> ExperimentResult:
        """
        Execute ML experiment (synchronous).
        
        Returns:
            ExperimentResult with ML outputs
        """
        # Step 1: Prepare data
        dataset = self.data_coordinator.prepare_dataset()
        splits = self.data_coordinator.create_splits(dataset)
        
        # Step 2: Train model
        model = self.training_coordinator.train_model(
            dataset=dataset,
            splits=splits
        )
        
        # Step 3: Evaluate
        signals = self.evaluation_coordinator.compute_signals(
            model=model,
            eval_data=splits.eval_data
        )
        auroc_scores = self.evaluation_coordinator.calculate_auroc(
            signals=signals,
            eval_labels=splits.eval_labels
        )
        
        # Step 4: Package results
        return ExperimentResult(
            auroc_scores=auroc_scores,
            eval_sizes=splits.eval_sizes,
            signal_table=signals,
            model_checkpoint=self.training_coordinator.checkpoint_path,
        )
    
    def save_results(self, results: ExperimentResult) -> Path:
        """
        Save results to disk (synchronous).
        
        Args:
            results: Experiment results
            
        Returns:
            Path to summary.json
        """
        summary_path = self.results_coordinator.save_all(
            results=results,
            config=self.config
        )
        results.summary_path = summary_path
        return summary_path
```

---

### 2. Backend Facade (Extends Base + Adds Database)

**File:** `backend/app/services/backend_experiment_facade.py`

```python
"""
Backend facade for experiments with database persistence.

Extends ExperimentFacade with:
- Database operations
- Async execution
- Progress tracking
- Status updates

Pattern: Adapter + Template Method
"""

import asyncio
from typing import Callable, Optional
from sqlalchemy.orm import Session

from uqlab.orchestration.experiment_facade import (
    ExperimentFacade,
    ExperimentResult,
)
from uqlab.shared.types import ExperimentConfig
from backend.app.models import UncertaintyExperiment
from backend.app.domain.value_objects import ExperimentStatus


class BackendExperimentFacade(ExperimentFacade):
    """
    Backend facade with database persistence.
    
    Extends base facade with:
    - Database CRUD operations
    - Async execution
    - Progress callbacks
    - Status tracking
    
    Use this for:
    - FastAPI endpoints
    - Streamlit backend
    - Batch experiments
    """
    
    def __init__(
        self,
        config: ExperimentConfig,
        db_session: Session,
        experiment_name: str,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        """
        Initialize with config + database session.
        
        Args:
            config: ML experiment config
            db_session: SQLAlchemy session
            experiment_name: Name for database record
            progress_callback: Optional progress updates
        """
        # Initialize base facade (ML logic)
        super().__init__(config)
        
        # Add backend-specific attributes
        self.db_session = db_session
        self.experiment_name = experiment_name
        self.progress_callback = progress_callback
        self.db_experiment: Optional[UncertaintyExperiment] = None
    
    async def run_and_persist(self) -> ExperimentResult:
        """
        Run experiment and persist to database (async).
        
        Template Method pattern:
        1. Create DB record (hook)
        2. Run ML experiment (inherited)
        3. Update DB with results (hook)
        
        Returns:
            ExperimentResult with database ID
        """
        try:
            # Hook 1: Create database record
            self._create_db_record()
            self._update_status(ExperimentStatus.RUNNING)
            self._report_progress("Initializing...", 0.0)
            
            # Core: Run ML experiment (inherited from base)
            result = await self._run_ml_experiment_async()
            
            # Hook 2: Persist results to database
            self._save_to_database(result)
            self._update_status(ExperimentStatus.COMPLETED)
            self._report_progress("Complete!", 1.0)
            
            return result
            
        except Exception as e:
            self._update_status(ExperimentStatus.FAILED, str(e))
            raise
    
    def _create_db_record(self):
        """Create initial database record"""
        self.db_experiment = UncertaintyExperiment(
            name=self.experiment_name,
            status=ExperimentStatus.PENDING,
            config=self.config.to_dict(),
        )
        self.db_session.add(self.db_experiment)
        self.db_session.commit()
    
    async def _run_ml_experiment_async(self) -> ExperimentResult:
        """
        Run ML experiment in thread pool (async wrapper).
        
        Wraps synchronous run_experiment() for async context.
        """
        # Report progress at key stages
        self._report_progress("Loading dataset...", 0.1)
        
        # Run synchronous ML code in thread pool
        result = await asyncio.to_thread(self.run_experiment)
        
        self._report_progress("Saving results...", 0.9)
        
        # Save to disk (inherited method)
        await asyncio.to_thread(self.save_results, result)
        
        return result
    
    def _save_to_database(self, result: ExperimentResult):
        """Persist ML results to database"""
        if not self.db_experiment:
            raise RuntimeError("Database record not created")
        
        # Update experiment record
        self.db_experiment.auroc_scores = result.auroc_scores
        self.db_experiment.eval_sizes = result.eval_sizes
        self.db_experiment.summary_path = str(result.summary_path)
        self.db_experiment.checkpoint_path = str(result.model_checkpoint)
        
        self.db_session.commit()
    
    def _update_status(
        self, 
        status: ExperimentStatus, 
        error_message: Optional[str] = None
    ):
        """Update experiment status in database"""
        if self.db_experiment:
            self.db_experiment.status = status
            if error_message:
                self.db_experiment.error_message = error_message
            self.db_session.commit()
    
    def _report_progress(self, message: str, progress: float):
        """Report progress via callback"""
        if self.progress_callback:
            self.progress_callback(message, progress)
```

---

### 3. FastAPI Integration

**File:** `backend/app/api/routes/experiments.py`

```python
"""
FastAPI routes using BackendExperimentFacade.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.backend_experiment_facade import (
    BackendExperimentFacade
)
from uqlab.shared.types import ExperimentConfig


router = APIRouter()


@router.post("/experiments")
async def create_experiment(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Create and run experiment via backend facade.
    
    Uses BackendExperimentFacade for:
    - Database persistence
    - Async execution
    - Progress tracking
    """
    try:
        # Parse config
        config = ExperimentConfig.from_dict(request["config"])
        
        # Create backend facade (with database)
        facade = BackendExperimentFacade(
            config=config,
            db_session=db,
            experiment_name=request["name"],
            progress_callback=None,  # Could add WebSocket here
        )
        
        # Run experiment (async + database)
        result = await facade.run_and_persist()
        
        # Return database record
        return {
            "id": facade.db_experiment.id,
            "name": facade.db_experiment.name,
            "status": facade.db_experiment.status,
            "auroc_scores": result.auroc_scores,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/{experiment_id}")
def get_experiment(
    experiment_id: int,
    db: Session = Depends(get_db)
):
    """Get experiment from database"""
    experiment = db.query(UncertaintyExperiment).get(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Not found")
    
    return {
        "id": experiment.id,
        "name": experiment.name,
        "status": experiment.status,
        "auroc_scores": experiment.auroc_scores,
        "created_at": experiment.created_at,
    }
```

---

### 4. CLI Script (Uses Base Facade)

**File:** `scripts/run_fast_uncertainty_classification.py`

```python
"""
CLI script using base ExperimentFacade.

No database, no async - pure ML.
"""

import argparse
from pathlib import Path

from uqlab.shared.types import ExperimentConfig
from uqlab.orchestration.experiment_facade import ExperimentFacade


def main():
    """Run experiment from CLI (no database)"""
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    
    # Load config
    config = ExperimentConfig.from_yaml(args.config)
    
    # Use base facade (no database)
    facade = ExperimentFacade(config)
    
    # Run experiment (synchronous)
    result = facade.run_experiment()
    summary_path = facade.save_results(result)
    
    print(f"✅ Complete! Results: {summary_path}")


if __name__ == "__main__":
    main()
```

---

## 🎯 Design Patterns Used

### 1. **Facade Pattern** (Gang of Four)
- **Base Facade:** Simplifies ML subsystem
- **Backend Facade:** Simplifies ML + database subsystem

### 2. **Adapter Pattern** (Gang of Four)
- `BackendExperimentFacade` adapts `ExperimentFacade` for database context

### 3. **Template Method Pattern** (Gang of Four)
- `run_and_persist()` defines algorithm skeleton
- Hooks: `_create_db_record()`, `_save_to_database()`
- Core: `run_experiment()` (inherited)

### 4. **Dependency Injection**
- `BackendExperimentFacade` receives `db_session` via constructor
- Enables testing with mock database

---

## 📊 Comparison Table

| Feature | ExperimentFacade (Base) | BackendExperimentFacade |
|---------|------------------------|-------------------------|
| **Purpose** | Pure ML experiments | ML + database persistence |
| **Dependencies** | ML libraries only | ML + SQLAlchemy + FastAPI |
| **Execution** | Synchronous | Async (wraps sync ML) |
| **Database** | ❌ No | ✅ Yes |
| **Progress Tracking** | ❌ No | ✅ Yes (callbacks) |
| **Use Cases** | CLI, notebooks, testing | FastAPI, Streamlit backend |
| **Complexity** | Low (5) | Medium (8) |
| **Testability** | ✅ Easy (no mocks) | ✅ Easy (mock db_session) |

---

## 🧪 Testing Strategy

### Test Base Facade (No Database)

```python
def test_experiment_facade_runs_ml():
    """Test pure ML logic without database"""
    config = ExperimentConfig.from_yaml("test_config.yaml")
    facade = ExperimentFacade(config)
    
    result = facade.run_experiment()
    
    assert result.auroc_scores is not None
    assert result.model_checkpoint.exists()
```

### Test Backend Facade (With Mock Database)

```python
@pytest.mark.asyncio
async def test_backend_facade_persists_to_db():
    """Test database persistence"""
    config = ExperimentConfig.from_yaml("test_config.yaml")
    mock_db = MagicMock(spec=Session)
    
    facade = BackendExperimentFacade(
        config=config,
        db_session=mock_db,
        experiment_name="test_exp"
    )
    
    result = await facade.run_and_persist()
    
    # Verify database calls
    assert mock_db.add.called
    assert mock_db.commit.called
    assert result.auroc_scores is not None
```

---

## 🚀 Migration Path

### Phase 1: Create Base Facade (Week 1)
1. ✅ Extract ML logic into `ExperimentFacade`
2. ✅ Update CLI script to use base facade
3. ✅ Add unit tests for base facade

### Phase 2: Create Backend Facade (Week 2)
4. ✅ Implement `BackendExperimentFacade` (extends base)
5. ✅ Add database persistence methods
6. ✅ Add async wrappers
7. ✅ Add progress tracking

### Phase 3: Integrate with FastAPI (Week 3)
8. ✅ Update FastAPI routes to use backend facade
9. ✅ Remove old `DirectExecutor` logic
10. ✅ Add integration tests

### Phase 4: Validation (Week 4)
11. ✅ Test CLI still works (base facade)
12. ✅ Test FastAPI works (backend facade)
13. ✅ Performance benchmarking
14. ✅ Deploy

---

## ✅ Benefits of This Architecture

### 1. **Separation of Concerns**
- ML logic: `ExperimentFacade` (no database)
- Backend logic: `BackendExperimentFacade` (adds database)

### 2. **Reusability**
- CLI uses base facade
- Backend uses extended facade
- Both share ML coordinators

### 3. **Testability**
- Test ML without database
- Test database without ML (mock base methods)

### 4. **Maintainability**
- Change ML logic: update base facade
- Change database schema: update backend facade
- No cross-contamination

### 5. **Performance**
- CLI: No database overhead
- Backend: Async for responsiveness

---

## 📚 References

1. **Gamma, E., et al. (1994).** *Design Patterns.* Addison-Wesley.
   - Facade Pattern (pp. 185-193)
   - Adapter Pattern (pp. 139-150)
   - Template Method (pp. 325-330)

2. **Martin, R. C. (2017).** *Clean Architecture.* Prentice Hall.
   - Dependency Rule (pp. 203-210)
   - Interface Adapters (pp. 211-218)

3. **Fowler, M. (2002).** *Patterns of Enterprise Application Architecture.* Addison-Wesley.
   - Service Layer (pp. 133-144)

---

**End of Dual Facade Architecture**

This architecture uses **inheritance + adapter pattern** to cleanly separate ML logic (base facade) from backend concerns (extended facade). The CLI uses the base, the backend extends it. Clean, testable, maintainable. 🎯