# PHASE 4: Migration Plan - Detailed Strategy

**Date:** 2026-06-19  
**Status:** 📋 Planning Complete, Ready for Implementation

## Executive Summary

PHASE 4 will refactor the 1,460-line monolithic script [`run_fast_uncertainty_classification.py`](scripts/run_fast_uncertainty_classification.py:1) into a clean, facade-based architecture. This migration will reduce the script to ~150 lines while maintaining full functionality.

## Current State Analysis

### Monolithic Script Structure (1,460 lines)

**Lines 1-100:** Imports and setup
- 50+ import statements
- Path configuration
- Logger setup

**Lines 101-400:** Argument parsing and configuration
- Complex argparse setup
- Configuration validation
- Default value handling

**Lines 401-800:** Data loading and preprocessing
- Dataset loading
- Feature extraction
- Train/val/test split creation
- Embedding organization

**Lines 801-1200:** Model training
- Model initialization
- Training loop
- Validation
- Checkpoint saving

**Lines 1201-1460:** Evaluation and results
- MC Dropout evaluation
- DualXDA signal computation
- AUROC calculation
- Results saving

## Migration Strategy

### Step 1: Create Facade-Based CLI Script (~150 lines)

**New File:** `scripts/run_experiment_facade.py`

```python
"""
Facade-based experiment runner - replaces monolithic script.
Uses ExperimentFacade for clean orchestration.
"""

import argparse
import logging
from pathlib import Path
from uqlab.facade import ExperimentFacade

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run uncertainty quantification experiment"
    )
    
    # Dataset configuration
    parser.add_argument("--dataset", default="cifar10n")
    parser.add_argument("--noise-type", default="worse_label")
    parser.add_argument("--under-supported", default="random:2")
    parser.add_argument("--under-train-per-class", type=int, default=50)
    parser.add_argument("--regular-train-per-class", type=int, default=300)
    
    # Model configuration
    parser.add_argument("--model-type", default="dinov2")
    parser.add_argument("--dinov2-model", default="small")
    parser.add_argument("--hidden-dim", type=int, default=256)
    parser.add_argument("--dropout", type=float, default=0.2)
    
    # Training configuration
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.0001)
    parser.add_argument("--batch-size", type=int, default=256)
    
    # Evaluation configuration
    parser.add_argument("--mc-passes", type=int, default=20)
    parser.add_argument("--eval-per-group", type=int, default=100)
    
    # Output configuration
    parser.add_argument("--output-dir", type=Path, default="results")
    parser.add_argument("--experiment-name", default=None)
    
    return parser.parse_args()

def build_config(args):
    """Build experiment configuration from arguments."""
    return {
        # Dataset
        "dataset_name": args.dataset,
        "noise_type": args.noise_type,
        "under_supported": args.under_supported,
        "under_train_per_class": args.under_train_per_class,
        "regular_train_per_class": args.regular_train_per_class,
        
        # Model
        "model_type": args.model_type,
        "dinov2_model": args.dinov2_model,
        "hidden_dim": args.hidden_dim,
        "dropout": args.dropout,
        
        # Training
        "epochs": args.epochs,
        "learning_rate": args.learning_rate,
        "weight_decay": args.weight_decay,
        "train_batch_size": args.batch_size,
        
        # Evaluation
        "mc_passes": args.mc_passes,
        "eval_per_group": args.eval_per_group,
        
        # Output
        "output_dir": str(args.output_dir),
        "experiment_name": args.experiment_name or f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
    }

def main():
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Build configuration
    config = build_config(args)
    
    logger.info(f"Starting experiment: {config['experiment_name']}")
    logger.info(f"Configuration: {json.dumps(config, indent=2)}")
    
    # Create facade and run experiment
    facade = ExperimentFacade(config, logger=logger)
    
    try:
        results = facade.run_experiment()
        
        logger.info("=" * 80)
        logger.info("Experiment Complete!")
        logger.info(f"Results saved to: {results['output_dir']}")
        logger.info("=" * 80)
        
        return 0
        
    except Exception as e:
        logger.error(f"Experiment failed: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

**Reduction:** 1,460 lines → ~150 lines (90% reduction)

### Step 2: Coordinator Integration

Each coordinator needs to integrate with existing components:

#### 2.1 DataCoordinator Integration

**Current:** Direct dataset loading in monolithic script  
**Target:** DataCoordinator wraps existing data loaders

```python
# In DataCoordinator.setup()
from uqlab.evaluation.classification.data_loader import (
    CIFAR10NDataset,
    sample_indices_for_fast_pilot,
)

def setup(self):
    # Load dataset
    self.dataset = CIFAR10NDataset(
        noise_type=self.config["noise_type"],
        under_supported=self.config["under_supported"],
        under_train_per_class=self.config["under_train_per_class"],
        regular_train_per_class=self.config["regular_train_per_class"],
    )
    
    # Create data loaders
    self.train_loader = DataLoader(
        self.dataset.train_dataset,
        batch_size=self.config["train_batch_size"],
        shuffle=True,
    )
    # ... val_loader, test_loader
```

#### 2.2 ModelCoordinator Integration

**Current:** Model creation scattered in script  
**Target:** ModelCoordinator uses model factory

```python
# In ModelCoordinator.get_model()
from uqlab.evaluation.classification.model_factory import build_model

def get_model(self):
    if self._model is None:
        self._model = build_model(
            model_type=self.config["model_type"],
            dinov2_model=self.config.get("dinov2_model", "small"),
            hidden_dim=self.config.get("hidden_dim", 256),
            dropout=self.config.get("dropout", 0.2),
            num_classes=10,  # CIFAR-10
        )
    return self._model
```

#### 2.3 TrainingCoordinator Integration

**Current:** Training loop in monolithic script  
**Target:** TrainingCoordinator orchestrates training

```python
# In TrainingCoordinator.train_epoch()
def train_epoch(self, model, train_loader, device):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0
    
    for batch_idx, (inputs, targets) in enumerate(train_loader):
        inputs, targets = inputs.to(device), targets.to(device)
        
        # Forward pass
        self.optimizer.zero_grad()
        outputs = model(inputs)
        loss = self.criterion(outputs, targets)
        
        # Backward pass
        loss.backward()
        self.optimizer.step()
        
        # Metrics
        total_loss += loss.item()
        _, predicted = outputs.max(1)
        total += targets.size(0)
        correct += predicted.eq(targets).sum().item()
    
    return {
        "loss": total_loss / len(train_loader),
        "accuracy": 100.0 * correct / total,
        "learning_rate": self.optimizer.param_groups[0]['lr'],
    }
```

#### 2.4 EvaluationCoordinator Integration

**Current:** Evaluation scattered across script  
**Target:** EvaluationCoordinator uses DualXDATracer

```python
# In EvaluationCoordinator.evaluate_model()
from uqlab.evaluation.legacy.triage.dualxda_axioms import DualXDATracer

def evaluate_model(self, model, test_loader, device):
    # Create tracer
    tracer = DualXDATracer(
        model=model,
        mc_passes=self.config["mc_passes"],
        device=device,
    )
    
    # Compute signals
    signals = tracer.compute_signals(test_loader)
    
    # Compute AUROC metrics
    auroc_metrics = self._compute_auroc_metrics(signals)
    
    return {
        "signals": signals,
        "auroc_metrics": auroc_metrics,
    }
```

#### 2.5 ResultCoordinator Integration

**Current:** Results saving scattered in script  
**Target:** ResultCoordinator centralizes result management

```python
# In ResultCoordinator.save_results()
def save_results(self, filename: str = "results.json"):
    output_path = Path(self.config["output_dir"]) / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(self.results, f, indent=2)
    
    self.logger.info(f"Results saved to: {output_path}")
```

### Step 3: FastAPI Route Updates

Update backend routes to use BackendExperimentFacade:

```python
# In backend/app/api/routes/experiments.py
from uqlab.facade import BackendExperimentFacade

@router.post("/experiments/{experiment_id}/run")
async def run_experiment(
    experiment_id: str,
    config: ExperimentConfig,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Create facade
    facade = BackendExperimentFacade(
        config=config.dict(),
        experiment_id=experiment_id,
        db_session=db
    )
    
    # Add progress callback for SSE
    def progress_callback(phase, progress, message):
        send_sse_update(experiment_id, phase, progress, message)
    
    facade.add_progress_callback(progress_callback)
    
    # Run in background
    background_tasks.add_task(facade.run_experiment_async)
    
    return {"status": "started", "experiment_id": experiment_id}
```

### Step 4: Testing Strategy

#### 4.1 Unit Tests

**Test each coordinator independently:**

```python
# tests/test_data_coordinator.py
def test_data_coordinator_setup():
    config = {...}
    coordinator = DataCoordinator(config)
    coordinator.setup()
    
    assert coordinator.train_loader is not None
    assert coordinator.val_loader is not None
    assert coordinator.test_loader is not None

# tests/test_model_coordinator.py
def test_model_coordinator_get_model():
    config = {"model_type": "dinov2", ...}
    coordinator = ModelCoordinator(config)
    coordinator.setup()
    
    model = coordinator.get_model()
    assert model is not None
    assert isinstance(model, nn.Module)
```

#### 4.2 Integration Tests

**Test facade orchestration:**

```python
# tests/test_experiment_facade.py
def test_experiment_facade_run():
    config = build_test_config()
    facade = ExperimentFacade(config)
    
    results = facade.run_experiment()
    
    assert "training_history" in results
    assert "evaluation_results" in results
    assert "final_metrics" in results
```

#### 4.3 End-to-End Tests

**Test complete workflow:**

```python
# tests/test_e2e_experiment.py
def test_full_experiment_workflow():
    # Run experiment via CLI
    result = subprocess.run([
        "python", "scripts/run_experiment_facade.py",
        "--epochs", "2",
        "--eval-per-group", "10",
    ], capture_output=True)
    
    assert result.returncode == 0
    assert Path("results").exists()
```

## Implementation Timeline

### Week 1: Core Integration
- ✅ Day 1-2: Create facade-based CLI script
- ✅ Day 3-4: Integrate DataCoordinator
- ✅ Day 5: Integrate ModelCoordinator

### Week 2: Training & Evaluation
- ✅ Day 1-2: Integrate TrainingCoordinator
- ✅ Day 3-4: Integrate EvaluationCoordinator
- ✅ Day 5: Integrate ResultCoordinator

### Week 3: Backend & Testing
- ✅ Day 1-2: Update FastAPI routes
- ✅ Day 3-4: Add unit tests
- ✅ Day 5: Add integration tests

### Week 4: Validation & Cleanup
- ✅ Day 1-2: End-to-end testing
- ✅ Day 3: Performance validation
- ✅ Day 4: Documentation updates
- ✅ Day 5: Remove old monolithic script

## Success Criteria

### Functional Requirements
- ✅ All existing functionality preserved
- ✅ CLI maintains backward compatibility
- ✅ Results match old implementation
- ✅ No performance regression

### Code Quality Metrics
- ✅ Cyclomatic complexity <10 per function
- ✅ Lines per function <50
- ✅ Code duplication <5%
- ✅ Test coverage >80%

### Maintainability
- ✅ Clear separation of concerns
- ✅ Easy to extend with new features
- ✅ Comprehensive documentation
- ✅ Type hints throughout

## Risk Mitigation

### Risk 1: Functionality Regression
**Mitigation:** Parallel testing with old script, comprehensive test suite

### Risk 2: Performance Degradation
**Mitigation:** Benchmark before/after, profile critical paths

### Risk 3: Integration Issues
**Mitigation:** Incremental integration, rollback plan via git

## Rollback Plan

If issues arise:
1. Revert to commit before PHASE 4 migration
2. Keep old script as `run_fast_uncertainty_classification_legacy.py`
3. Gradual migration with feature flags

## Next Steps

1. **Immediate:** Create `scripts/run_experiment_facade.py`
2. **Short-term:** Integrate coordinators one by one
3. **Medium-term:** Update FastAPI routes
4. **Long-term:** Complete testing and validation

---

**Status:** 📋 Plan complete, ready for implementation  
**Estimated Effort:** 4 weeks (1 developer)  
**Risk Level:** Medium (mitigated by incremental approach)

*Made with Bob*