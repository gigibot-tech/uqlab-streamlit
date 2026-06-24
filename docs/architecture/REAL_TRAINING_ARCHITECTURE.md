# Real ML Training Architecture

## Overview

This document describes the modular, production-ready architecture for real ML training in the uqlab-streamlit project using clean architecture principles and design patterns.

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     API Layer (FastAPI)                      │
│  POST /experiments/{id}/start → Start real training         │
│  GET  /experiments/{id}       → Get experiment status       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer (Business Logic)             │
│                                                              │
│  TrainingOrchestrator (Facade Pattern)                      │
│    - Coordinates training workflow                          │
│    - Manages async job execution                            │
│    - Handles errors and cleanup                             │
│                              ↓                               │
│  TrainingExecutor (Strategy Pattern)                        │
│    - DirectExecutor: in-process uqlab.runner.pipeline.run   │
│    - DockerExecutor: Run in container (future)              │
│    - KubernetesExecutor: Run in K8s (future)                │
│                              ↓                               │
│  ProgressParser (Observer Pattern)                          │
│    - Parse stdout for progress updates                      │
│    - Extract epoch/stage information                        │
│    - Notify repository of changes                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Repository Layer (Data Access)              │
│                                                              │
│  ExperimentRepository                                       │
│    - CRUD operations for experiments                        │
│    - Update status and progress                             │
│    - Save training results                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer (Models)                     │
│                                                              │
│  TrainingConfig (Value Object)                              │
│    - Immutable training configuration                       │
│    - Converts to YAML for ML script                         │
│                                                              │
│  TrainingResult (Value Object)                              │
│    - Immutable training results                             │
│    - AUROC scores and metadata                              │
│                                                              │
│  ProgressUpdate (Value Object)                              │
│    - Immutable progress snapshot                            │
│    - Stage, percentage, message                             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                ML Core (uqlab.runner — in-process)           │
│  uqlab.runner.pipeline.run(config_path, output_dir)           │
│    - Loads ExperimentConfig from YAML                        │
│    - run_experiment_core: train + evaluate + artifacts       │
└─────────────────────────────────────────────────────────────┘
```

## Design Patterns Used

### 1. **Facade Pattern** - `TrainingOrchestrator`
Simplifies complex training workflow into a single interface.

```python
orchestrator = TrainingOrchestrator(executor, repository)
await orchestrator.start_training(experiment_id)
```

### 2. **Strategy Pattern** - `TrainingExecutor`
Pluggable execution strategies for different environments.

```python
class TrainingExecutor(ABC):
    @abstractmethod
    async def execute(config_path, output_dir, progress_callback) -> TrainingResult:
        pass

class DirectExecutor(TrainingExecutor):
    # In-process: calls uqlab.runner.pipeline.run (thread pool)

class DockerExecutor(TrainingExecutor):
    # Container execution (future)
```

### 3. **Repository Pattern** - `ExperimentRepository`
Abstracts data access from business logic.

```python
repository = ExperimentRepository(session)
repository.update_status(exp_id, JobStatus.RUNNING, 0.5)
repository.save_results(exp_id, results)
```

### 4. **Value Object Pattern** - Domain Models
Immutable, validated data structures.

```python
config = TrainingConfig(
    epochs=12,
    learning_rate=0.001,
    # ... validated parameters
)
```

## File Structure

```
backend/app/
├── domain/                          # Domain layer (business entities)
│   ├── __init__.py
│   ├── models.py                    # TrainingConfig, TrainingResult (50 LOC)
│   └── value_objects.py             # ProgressUpdate, TrainingStage (54 LOC)
│
├── repositories/                    # Data access layer
│   ├── __init__.py
│   └── experiment_repository.py     # ExperimentRepository (102 LOC)
│
├── services/                        # Business logic layer
│   ├── __init__.py
│   ├── training_orchestrator.py     # TrainingOrchestrator (70 LOC)
│   ├── progress_parser.py           # ProgressParser (45 LOC)
│   └── executors/
│       ├── __init__.py
│       ├── base.py                  # TrainingExecutor interface (36 LOC)
│       └── direct_executor.py       # DirectExecutor (in-process pipeline.run)
│
└── api/
    └── routes/
        └── experiments.py           # API endpoints (updated)
```

## Workflow Sequence

### 1. Create Experiment
```
User → Streamlit → POST /experiments/no-auth
                → Create experiment record in DB
                → Status: QUEUED
```

### 2. Start Training
```
User clicks "Start" → POST /experiments/{id}/start
                   → TrainingOrchestrator.start_training()
                   → Write config YAML
                   → DirectExecutor.execute() (in-process)
                   → pipeline.run() → run_experiment_core()
                   → Status: RUNNING
```

### 3. Progress Tracking
```
ML pipeline progress → progress_callback(ProgressUpdate)
                    → ExperimentRepository.update_status()
                    → Update DB (progress, message)
```

### 4. Completion
```
Pipeline finishes → Writes summary.json + results.pt
                  → DirectExecutor._read_results()
                  → ExperimentRepository.save_results()
                  → Status: COMPLETED
                  → AUROC scores saved
```

### 5. Auto-Refresh (Frontend)
```
Streamlit auto-poll → GET /experiments/no-auth
                    → Display updated progress
                    → Show AUROC scores when complete
```

## Key Benefits

### ✅ Separation of Concerns
- Domain logic isolated from infrastructure
- ML core (`uqlab.runner`) invoked in-process via `DirectExecutor`
- Easy to test each layer independently

### ✅ Extensibility
- Add new executors (Docker, K8s) without changing core logic
- Swap ML script without touching backend code
- Add new progress parsers for different output formats

### ✅ Maintainability
- Small, focused files (30-50 LOC each)
- Clear responsibilities per class
- Single Responsibility Principle

### ✅ Testability
- Mock executors for unit tests
- Mock repository for service tests
- No need to run actual ML for testing

### ✅ Production-Ready
- Async execution (non-blocking)
- Proper error handling
- Progress tracking
- Result persistence

## Configuration

Production training uses `DirectExecutor`, which calls `uqlab.runner.pipeline.run` with the experiment's `config.yaml`. CLI dev path: `scripts/runners/run_fast_uncertainty_classification.py` (same pipeline entry).

**Note:** `SubprocessExecutor` was removed (2026-06-24); it had been retired in favor of in-process execution.

### Dependencies
Added to `backend/pyproject.toml`:
```toml
dependencies = [
    # ... existing deps
    "pyyaml>=6.0",
]
```

## Usage

### Start Backend
```bash
cd uqlab-streamlit/backend
python -m uvicorn app.main:app --reload
```

### Start Streamlit
```bash
cd uqlab-streamlit
./run_streamlit.sh
```

### Create and Start Experiment
1. Fill experiment form in Streamlit
2. Click "Create Experiment"
3. Click "Start: exp_name" button
4. Enable "Auto-Refresh" to watch progress
5. View AUROC scores when complete

## Future Enhancements

### 1. Docker Executor
```python
class DockerExecutor(TrainingExecutor):
    async def execute(...):
        # Run ML script in Docker container
        # Better isolation and reproducibility
```

### 2. Kubernetes Executor
```python
class KubernetesExecutor(TrainingExecutor):
    async def execute(...):
        # Submit K8s Job
        # Production-scale training
```

### 3. Progress Streaming
```python
# WebSocket for real-time progress
@router.websocket("/experiments/{id}/progress")
async def stream_progress(websocket: WebSocket, id: UUID):
    # Stream progress updates to frontend
```

### 4. Result Caching
```python
# Cache results for faster retrieval
class CachedExperimentRepository(ExperimentRepository):
    def __init__(self, session, cache):
        self.cache = cache  # Redis, etc.
```

## Troubleshooting

### Training Fails Immediately
```
Check: uqlab import path (PYTHONPATH includes src/)
Check: Config YAML is valid
Check: Output directory is writable
```

### Progress Not Updating
```
Check: ProgressParser regex patterns match ML script output
Check: Database connection is active
Check: Repository update_status is being called
```

## Summary

This architecture provides a **clean, modular, production-ready** solution for real ML training with:
- ✅ Proper separation of concerns
- ✅ Design patterns (Facade, Strategy, Repository, Value Object)
- ✅ Async execution
- ✅ Progress tracking
- ✅ Extensible and testable
- ✅ All files kept concise (30-50 LOC)

**Commit:** `bed8450` - "Implement modular real ML training pipeline with clean architecture"