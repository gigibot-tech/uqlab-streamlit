# Phase 4: Facade Integration Implementation Plan

**Status:** Ready to Execute  
**Created:** 2026-06-19  
**Goal:** Make the facade architecture functional by integrating with existing components

---

## Executive Summary

The facade architecture (Phases 1-3) is complete but not yet functional. This document provides a step-by-step implementation plan to:

1. Connect coordinators to existing data loaders and models
2. Make `run_experiment_facade.py` executable
3. Update FastAPI routes to use `BackendExperimentFacade`
4. Validate the integration works end-to-end

**Estimated Effort:** 3-5 days of focused development

---

## Current State Analysis

### ✅ What's Complete

**Phase 1: Pre-Refactoring Audit**
- Component reuse analysis (147 classes discovered)
- Dead code archival (106 components moved)
- Comprehensive documentation

**Phase 2: Facade Architecture**
- 5 specialized coordinators (Data, Model, Training, Evaluation, Result)
- `ExperimentFacade` main orchestrator (418 lines)
- Clean separation of concerns

**Phase 3: Backend Extension**
- `BackendExperimentFacade` with async support
- Progress callback system
- Database persistence methods
- Status management (pending/running/completed/failed/cancelled)

**Phase 4: Initial Work**
- Facade-based CLI script created (310 lines, 79% reduction)
- Migration plan documented
- Usage analysis complete

### ❌ What's Missing

1. **Coordinator Integration**: Coordinators don't yet use existing components
2. **Import Resolution**: Facade needs proper imports for CIFAR10N, models, etc.
3. **Configuration Mapping**: Need to map facade config to existing component APIs
4. **API Route Updates**: FastAPI routes still use old execution path
5. **Testing**: No tests for facade components yet

---

## Implementation Steps

### Step 1: DataCoordinator Integration (Priority: HIGH)

**File:** `src/uqlab/facade/coordinators/data_coordinator.py`

**Current State:** Stub implementation with TODOs

**Required Changes:**

```python
# Add imports
from uqlab.evaluation.classification.data_loader import CIFAR10NDataset

# Update setup() method
def setup(self) -> None:
    """Load and prepare datasets."""
    dataset_name = self.config.get('dataset_name', 'cifar10n')
    noise_type = self.config.get('noise_type', 'worse_label')
    
    # Parse under-supported classes
    under_supported_str = self.config.get('under_supported', 'random:2')
    if under_supported_str.startswith('random:'):
        num_under = int(under_supported_str.split(':')[1])
        under_supported = list(np.random.choice(10, num_under, replace=False))
    else:
        under_supported = [int(x.strip()) for x in under_supported_str.split(',')]
    
    # Create dataset instance
    self.dataset = CIFAR10NDataset(
        noise_type=noise_type,
        under_supported_classes=under_supported,
        under_train_per_class=self.config.get('under_train_per_class', 50),
        regular_train_per_class=self.config.get('regular_train_per_class', 300),
        eval_per_group=self.config.get('eval_per_group', 100),
        seed=self.config.get('seed', 42)
    )
    
    # Load data
    self.train_loader = self.dataset.get_train_loader(
        batch_size=self.config.get('train_batch_size', 256)
    )
    self.eval_loaders = self.dataset.get_eval_loaders()
    
    self.logger.info(f"✅ Loaded {dataset_name} with {noise_type} noise")
    self.logger.info(f"   Under-supported classes: {under_supported}")
    self.logger.info(f"   Training samples: {len(self.dataset.train_dataset)}")
```

**Files to Read:**
- `src/uqlab/evaluation/classification/data_loader.py` (CIFAR10NDataset API)

**Validation:**
- Can instantiate CIFAR10NDataset
- Can get train/eval loaders
- Handles random vs explicit under-supported classes

---

### Step 2: ModelCoordinator Integration (Priority: HIGH)

**File:** `src/uqlab/facade/coordinators/model_coordinator.py`

**Current State:** Stub implementation with TODOs

**Required Changes:**

```python
# Add imports
from uqlab.models.embedding_dropout_mlp import EmbeddingDropoutMLP
from uqlab.models.resnet_feature_extractor import ResNetFeatureExtractor
import torch

# Update setup() method
def setup(self) -> None:
    """Initialize model based on configuration."""
    model_type = self.config.get('model_type', 'dinov2')
    num_classes = self.config.get('num_classes', 10)
    
    if model_type == 'dinov2':
        dinov2_model = self.config.get('dinov2_model', 'small')
        hidden_dim = self.config.get('hidden_dim', 256)
        dropout = self.config.get('dropout', 0.2)
        
        self.model = EmbeddingDropoutMLP(
            dinov2_model=dinov2_model,
            hidden_dim=hidden_dim,
            num_classes=num_classes,
            dropout=dropout
        )
        self.logger.info(f"✅ Created DINOv2-{dinov2_model} model")
        
    elif model_type == 'resnet':
        use_untrained = self.config.get('use_untrained_resnet', False)
        
        self.model = ResNetFeatureExtractor(
            num_classes=num_classes,
            pretrained=not use_untrained,
            freeze_backbone=True  # Feature extraction mode
        )
        self.logger.info(f"✅ Created ResNet model (pretrained={not use_untrained})")
    
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    # Move to device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    self.model = self.model.to(device)
    self.device = device
    
    self.logger.info(f"   Device: {device}")
    self.logger.info(f"   Parameters: {sum(p.numel() for p in self.model.parameters()):,}")
```

**Files to Read:**
- `src/uqlab/models/embedding_dropout_mlp.py`
- `src/uqlab/models/resnet_feature_extractor.py`

**Validation:**
- Can create DINOv2 models (small/base/large/giant)
- Can create ResNet models (pretrained/untrained)
- Handles device placement correctly

---

### Step 3: TrainingCoordinator Integration (Priority: HIGH)

**File:** `src/uqlab/facade/coordinators/training_coordinator.py`

**Current State:** Stub implementation with TODOs

**Required Changes:**

```python
# Add imports
import torch
import torch.nn as nn
import torch.optim as optim
from tqdm import tqdm

# Update setup() method
def setup(self) -> None:
    """Setup training components."""
    # Get model and device from ModelCoordinator
    self.model = self.dependencies['model'].model
    self.device = self.dependencies['model'].device
    
    # Get data loader from DataCoordinator
    self.train_loader = self.dependencies['data'].train_loader
    
    # Setup optimizer
    learning_rate = self.config.get('learning_rate', 0.001)
    weight_decay = self.config.get('weight_decay', 0.0001)
    
    self.optimizer = optim.Adam(
        self.model.parameters(),
        lr=learning_rate,
        weight_decay=weight_decay
    )
    
    # Setup loss function
    self.criterion = nn.CrossEntropyLoss()
    
    self.logger.info(f"✅ Training setup complete")
    self.logger.info(f"   Optimizer: Adam (lr={learning_rate}, wd={weight_decay})")

# Update train() method
def train(self) -> Dict[str, Any]:
    """Execute training loop."""
    epochs = self.config.get('epochs', 12)
    
    training_history = {
        'epoch_losses': [],
        'epoch_accuracies': []
    }
    
    self.model.train()
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        correct = 0
        total = 0
        
        pbar = tqdm(self.train_loader, desc=f"Epoch {epoch+1}/{epochs}")
        
        for batch_idx, (inputs, targets) in enumerate(pbar):
            inputs, targets = inputs.to(self.device), targets.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.criterion(outputs, targets)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Track metrics
            epoch_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
            # Update progress bar
            pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'acc': f'{100.*correct/total:.2f}%'
            })
        
        # Epoch summary
        avg_loss = epoch_loss / len(self.train_loader)
        accuracy = 100. * correct / total
        
        training_history['epoch_losses'].append(avg_loss)
        training_history['epoch_accuracies'].append(accuracy)
        
        self.logger.info(f"Epoch {epoch+1}/{epochs}: Loss={avg_loss:.4f}, Acc={accuracy:.2f}%")
    
    return training_history
```

**Files to Read:**
- Existing training loops in `scripts/run_fast_uncertainty_classification.py`

**Validation:**
- Training loop executes without errors
- Loss decreases over epochs
- Accuracy improves over epochs

---

### Step 4: EvaluationCoordinator Integration (Priority: HIGH)

**File:** `src/uqlab/facade/coordinators/evaluation_coordinator.py`

**Current State:** Stub implementation with TODOs

**Required Changes:**

```python
# Add imports
import torch
import numpy as np
from uqlab.evaluation.uncertainty_metrics import compute_uncertainty_signals

# Update setup() method
def setup(self) -> None:
    """Setup evaluation components."""
    # Get model and device
    self.model = self.dependencies['model'].model
    self.device = self.dependencies['model'].device
    
    # Get evaluation loaders
    self.eval_loaders = self.dependencies['data'].eval_loaders
    
    # Get MC passes configuration
    self.mc_passes = self.config.get('mc_passes', 20)
    
    self.logger.info(f"✅ Evaluation setup complete")
    self.logger.info(f"   MC Dropout passes: {self.mc_passes}")

# Update evaluate() method
def evaluate(self) -> Dict[str, Any]:
    """Run evaluation with uncertainty quantification."""
    self.model.eval()
    
    results = {}
    
    for group_name, loader in self.eval_loaders.items():
        self.logger.info(f"Evaluating {group_name}...")
        
        # Collect predictions with MC Dropout
        all_predictions = []
        all_targets = []
        all_mc_predictions = []
        
        with torch.no_grad():
            for inputs, targets in loader:
                inputs = inputs.to(self.device)
                
                # Standard prediction
                outputs = self.model(inputs)
                predictions = torch.softmax(outputs, dim=1)
                all_predictions.append(predictions.cpu().numpy())
                all_targets.append(targets.numpy())
                
                # MC Dropout predictions
                mc_preds = []
                for _ in range(self.mc_passes):
                    # Enable dropout during inference
                    self.model.train()  # Enables dropout
                    mc_outputs = self.model(inputs)
                    mc_preds.append(torch.softmax(mc_outputs, dim=1).cpu().numpy())
                    self.model.eval()  # Disable dropout
                
                all_mc_predictions.append(np.stack(mc_preds, axis=0))
        
        # Concatenate results
        predictions = np.concatenate(all_predictions, axis=0)
        targets = np.concatenate(all_targets, axis=0)
        mc_predictions = np.concatenate(all_mc_predictions, axis=1)
        
        # Compute uncertainty signals
        signals = compute_uncertainty_signals(
            predictions=predictions,
            mc_predictions=mc_predictions,
            targets=targets
        )
        
        results[group_name] = {
            'predictions': predictions,
            'targets': targets,
            'signals': signals,
            'accuracy': (predictions.argmax(axis=1) == targets).mean()
        }
        
        self.logger.info(f"   {group_name}: Accuracy={results[group_name]['accuracy']:.4f}")
    
    return results
```

**Files to Read:**
- `src/uqlab/evaluation/uncertainty_metrics.py`
- Existing evaluation code in scripts

**Validation:**
- MC Dropout works correctly
- Uncertainty signals computed
- Results match expected format

---

### Step 5: ResultCoordinator Integration (Priority: MEDIUM)

**File:** `src/uqlab/facade/coordinators/result_coordinator.py`

**Current State:** Stub implementation with TODOs

**Required Changes:**

```python
# Add imports
import json
from pathlib import Path
import pickle

# Update setup() method
def setup(self) -> None:
    """Setup result storage."""
    output_dir = Path(self.config.get('output_dir', 'results'))
    experiment_name = self.config.get('experiment_name', 'experiment')
    
    self.output_path = output_dir / experiment_name
    self.output_path.mkdir(parents=True, exist_ok=True)
    
    self.logger.info(f"✅ Results will be saved to: {self.output_path}")

# Update save_results() method
def save_results(self, results: Dict[str, Any]) -> str:
    """Save experiment results to disk."""
    # Save training history
    if 'training_history' in results:
        with open(self.output_path / 'training_history.json', 'w') as f:
            json.dump(results['training_history'], f, indent=2)
    
    # Save evaluation results
    if 'evaluation_results' in results:
        # Save as pickle for full data
        with open(self.output_path / 'evaluation_results.pkl', 'wb') as f:
            pickle.dump(results['evaluation_results'], f)
        
        # Save summary as JSON
        summary = {}
        for group, data in results['evaluation_results'].items():
            summary[group] = {
                'accuracy': float(data['accuracy']),
                'num_samples': len(data['targets'])
            }
        
        with open(self.output_path / 'evaluation_summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
    
    # Save model checkpoint
    if 'model_state' in results:
        torch.save(
            results['model_state'],
            self.output_path / 'model_checkpoint.pt'
        )
    
    # Save configuration
    with open(self.output_path / 'config.json', 'w') as f:
        json.dump(self.config, f, indent=2)
    
    self.logger.info(f"✅ Results saved to: {self.output_path}")
    
    return str(self.output_path)
```

**Validation:**
- Files created in correct location
- JSON files are valid
- Pickle files can be loaded

---

### Step 6: Update FastAPI Routes (Priority: HIGH)

**File:** `backend/app/api/routes/experiments.py`

**Current Changes Needed:**

```python
# Add import
from uqlab.facade import BackendExperimentFacade

# Update create_experiment endpoint (around line 100)
@router.post("/no-auth", response_model=ExperimentResponse)
async def create_experiment_no_auth(
    payload: ExperimentCreate,
    session: SessionDep,
) -> Any:
    """Create and run experiment using facade pattern."""
    
    # Get or create test user
    test_user = get_or_create_test_user(session)
    
    # Create experiment record
    experiment = UncertaintyExperiment(
        name=payload.name,
        config=payload.config,
        status=JobStatus.PENDING,
        created_by_id=test_user.id,
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)
    
    # Create facade with database session
    facade = BackendExperimentFacade(
        config=payload.config,
        experiment_id=experiment.id,
        db_session=session,
        logger=logger
    )
    
    # Add progress callback
    def progress_callback(stage: str, progress: float, message: str):
        logger.info(f"[{experiment.id}] {stage}: {progress:.1%} - {message}")
    
    facade.add_progress_callback(progress_callback)
    
    # Run experiment asynchronously
    try:
        results = await facade.run_experiment_async()
        
        # Update experiment with results
        experiment.status = JobStatus.COMPLETED
        experiment.result_summary = results.get('summary', {})
        session.commit()
        
    except Exception as e:
        experiment.status = JobStatus.FAILED
        experiment.error_message = str(e)
        session.commit()
        raise
    
    return experiment
```

**Validation:**
- Experiment creates successfully
- Progress updates work
- Results saved to database
- Error handling works

---

### Step 7: Update CLI Script (Priority: MEDIUM)

**File:** `scripts/run_experiment_facade.py`

**Current State:** Complete but needs testing

**Required Changes:**
- None needed - script is ready
- Just needs coordinators to be functional

**Testing:**
```bash
# Test basic execution
python scripts/run_experiment_facade.py --epochs 2 --mc-passes 5

# Test with custom config
python scripts/run_experiment_facade.py \
    --epochs 10 \
    --mc-passes 20 \
    --under-supported "0,1" \
    --under-train-per-class 100 \
    --regular-train-per-class 500
```

---

### Step 8: Add Unit Tests (Priority: MEDIUM)

**New Files to Create:**

1. `tests/unit/facade/test_data_coordinator.py`
2. `tests/unit/facade/test_model_coordinator.py`
3. `tests/unit/facade/test_training_coordinator.py`
4. `tests/unit/facade/test_evaluation_coordinator.py`
5. `tests/unit/facade/test_result_coordinator.py`
6. `tests/unit/facade/test_experiment_facade.py`

**Example Test Structure:**

```python
# tests/unit/facade/test_data_coordinator.py
import pytest
from uqlab.facade.coordinators import DataCoordinator

def test_data_coordinator_setup():
    """Test DataCoordinator can load CIFAR10N."""
    config = {
        'dataset_name': 'cifar10n',
        'noise_type': 'worse_label',
        'under_supported': 'random:2',
        'under_train_per_class': 50,
        'regular_train_per_class': 300,
        'eval_per_group': 100,
        'seed': 42
    }
    
    coordinator = DataCoordinator(config)
    coordinator.setup()
    
    assert coordinator.train_loader is not None
    assert coordinator.eval_loaders is not None
    assert len(coordinator.eval_loaders) == 4  # 4 evaluation groups

def test_data_coordinator_explicit_classes():
    """Test explicit under-supported classes."""
    config = {
        'dataset_name': 'cifar10n',
        'noise_type': 'worse_label',
        'under_supported': '0,1,2',
        'under_train_per_class': 50,
        'regular_train_per_class': 300,
        'eval_per_group': 100,
        'seed': 42
    }
    
    coordinator = DataCoordinator(config)
    coordinator.setup()
    
    # Verify under-supported classes are [0, 1, 2]
    assert coordinator.dataset.under_supported_classes == [0, 1, 2]
```

---

### Step 9: Integration Testing (Priority: HIGH)

**New File:** `tests/integration/test_facade_end_to_end.py`

```python
import pytest
from uqlab.facade import ExperimentFacade

def test_full_experiment_execution():
    """Test complete experiment execution through facade."""
    config = {
        'experiment_name': 'test_experiment',
        'dataset_name': 'cifar10n',
        'noise_type': 'worse_label',
        'under_supported': 'random:2',
        'under_train_per_class': 50,
        'regular_train_per_class': 100,  # Small for testing
        'model_type': 'dinov2',
        'dinov2_model': 'small',
        'hidden_dim': 128,
        'dropout': 0.2,
        'epochs': 2,  # Quick test
        'learning_rate': 0.001,
        'weight_decay': 0.0001,
        'train_batch_size': 64,
        'mc_passes': 5,  # Quick test
        'eval_per_group': 50,
        'output_dir': '/tmp/test_facade',
        'seed': 42
    }
    
    facade = ExperimentFacade(config)
    results = facade.run_experiment()
    
    # Verify results structure
    assert 'training_history' in results
    assert 'evaluation_results' in results
    assert 'output_dir' in results
    
    # Verify training happened
    assert len(results['training_history']['epoch_losses']) == 2
    
    # Verify evaluation happened
    assert len(results['evaluation_results']) == 4  # 4 groups
    
    # Verify files created
    output_path = Path(results['output_dir'])
    assert (output_path / 'config.json').exists()
    assert (output_path / 'training_history.json').exists()
    assert (output_path / 'evaluation_summary.json').exists()
```

---

## Implementation Order

### Week 1: Core Integration

**Day 1-2: Data & Model Coordinators**
- [ ] Implement DataCoordinator.setup()
- [ ] Implement ModelCoordinator.setup()
- [ ] Test data loading works
- [ ] Test model creation works

**Day 3-4: Training & Evaluation**
- [ ] Implement TrainingCoordinator.train()
- [ ] Implement EvaluationCoordinator.evaluate()
- [ ] Test training loop works
- [ ] Test evaluation works

**Day 5: Results & Integration**
- [ ] Implement ResultCoordinator.save_results()
- [ ] Test end-to-end execution
- [ ] Fix any integration issues

### Week 2: API & Testing

**Day 6-7: FastAPI Integration**
- [ ] Update experiments.py route
- [ ] Test API endpoint works
- [ ] Add progress tracking
- [ ] Test error handling

**Day 8-9: Testing**
- [ ] Write unit tests for coordinators
- [ ] Write integration tests
- [ ] Achieve >80% code coverage
- [ ] Fix any bugs found

**Day 10: Documentation & Cleanup**
- [ ] Update README files
- [ ] Add usage examples
- [ ] Create migration guide
- [ ] Mark old script as deprecated

---

## Success Criteria

### Functional Requirements

✅ **Must Have:**
1. CLI script executes successfully
2. API endpoint creates and runs experiments
3. Results saved to correct location
4. All coordinators work with real data
5. Training converges (loss decreases)
6. Evaluation produces valid metrics

✅ **Should Have:**
7. Unit tests pass (>80% coverage)
8. Integration tests pass
9. Progress callbacks work
10. Error handling works correctly

✅ **Nice to Have:**
11. Performance matches old script
12. Documentation complete
13. Migration guide available

### Non-Functional Requirements

- **Performance:** No more than 10% slower than old script
- **Reliability:** No crashes on valid inputs
- **Maintainability:** Code follows SOLID principles
- **Testability:** All components have unit tests

---

## Risk Mitigation

### Risk 1: Import Errors

**Mitigation:**
- Test imports incrementally
- Use try/except with helpful error messages
- Document all dependencies

### Risk 2: Configuration Mismatches

**Mitigation:**
- Create configuration validation
- Add clear error messages
- Provide configuration examples

### Risk 3: Performance Regression

**Mitigation:**
- Profile both old and new implementations
- Optimize bottlenecks
- Consider async execution

### Risk 4: Breaking Changes

**Mitigation:**
- Keep old script functional during migration
- Add deprecation warnings
- Provide migration guide

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Set up development environment** with all dependencies
3. **Create feature branch** for facade integration
4. **Start with Step 1** (DataCoordinator)
5. **Test incrementally** after each step
6. **Document progress** in this file

---

## Progress Tracking

| Step | Status | Assignee | Completion Date |
|------|--------|----------|-----------------|
| 1. DataCoordinator | 🔴 Not Started | - | - |
| 2. ModelCoordinator | 🔴 Not Started | - | - |
| 3. TrainingCoordinator | 🔴 Not Started | - | - |
| 4. EvaluationCoordinator | 🔴 Not Started | - | - |
| 5. ResultCoordinator | 🔴 Not Started | - | - |
| 6. FastAPI Routes | 🔴 Not Started | - | - |
| 7. CLI Script Testing | 🔴 Not Started | - | - |
| 8. Unit Tests | 🔴 Not Started | - | - |
| 9. Integration Tests | 🔴 Not Started | - | - |

**Legend:**
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Complete
- ⚠️ Blocked

---

## References

- [PHASE_2_FACADE_ARCHITECTURE.md](PHASE_2_FACADE_ARCHITECTURE.md) - Original facade design
- [PHASE_3_BACKEND_FACADE_COMPLETE.md](PHASE_3_BACKEND_FACADE_COMPLETE.md) - Backend extension
- [PHASE_4_MIGRATION_PLAN.md](PHASE_4_MIGRATION_PLAN.md) - Migration strategy
- [src/uqlab/facade/README.md](src/uqlab/facade/README.md) - Facade documentation

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-19  
**Status:** Ready for Implementation