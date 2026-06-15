# Sweep System Consolidation

## Overview
Both sweep systems now use the unified `run_fast_uncertainty_classification.py` script.

## Sweep Types

### 1. Attribution-Based Sweeps (DualXDA)
- Uses DINOv2, CNN, or ResNet architectures
- Computes 7 attribution signals
- Endpoint: `POST /api/v1/batch-experiments`

### 2. Benchmark Sweeps (Gaussian Logits, IT)
- Uses standard UQ methods
- Direct uncertainty estimates
- Endpoint: `POST /api/v1/uq-benchmarks/sweep` (deprecated, use batch-experiments)

## Migration Guide

### Old uq_benchmarks sweep:
```python
POST /api/v1/uq-benchmarks/label-noise-sweep
{
  "method_name": "gaussian_logits",
  "noise_rates": [0.0, 0.1, 0.2]
}
```

### New unified sweep:
```python
POST /api/v1/batch-experiments
{
  "name": "gaussian_logits_sweep",
  "method_type": "benchmark",
  "base_config": {
    "architecture": "cnn_mcdropout",
    "training_mode": "end_to_end",
    "noise_type": "worse_label",
    "under_supported_classes": "3,5",
    "under_train_per_class": 50,
    "regular_train_per_class": 300,
    "eval_per_group": 600,
    "hidden_dim": 128,
    "dropout": 0.5,
    "epochs": 12,
    "learning_rate": 0.001,
    "weight_decay": 0.0001,
    "train_batch_size": 128,
    "mc_passes": 20
  },
  "sweep_definitions": [{
    "parameter": "aleatoric_noise_percentage",
    "value_type": "float",
    "range": {"start": 0.0, "end": 0.2, "step": 0.1}
  }]
}
```

## Unified Architecture

Both sweep types now:
1. Use the same configuration format (YAML-based)
2. Execute through `run_fast_uncertainty_classification.py`
3. Store results in the same database tables
4. Support the same parameter sweep syntax
5. Use the same batch execution service

## Benefits

1. **Single Entry Point**: One script handles all experiments
2. **Consistent Configuration**: Same YAML format for all methods
3. **Unified Storage**: All results in same database schema
4. **Flexible Architectures**: Easy to add new model types
5. **Simplified Maintenance**: One codebase to maintain

## Architecture Support

### Attribution Methods (method_type="attribution")
- `dinov2_mlp`: DINOv2 + MLP classifier
- `cnn_mcdropout`: Custom CNN with MC Dropout
- `resnet18_mcdropout`: ResNet18 with MC Dropout

### Benchmark Methods (method_type="benchmark")
- `gaussian_logits`: Gaussian distribution over logits
- `information_theoretic`: IT-based uncertainty
- Any architecture above can be used as backbone

## Example: Complete Sweep Configuration

```yaml
# Attribution-based sweep
name: "dinov2_noise_sweep"
method_type: "attribution"
base_config:
  architecture: dinov2_mlp
  training_mode: feature_space
  dinov2_model: small
  hidden_dim: 256
  dropout: 0.2
  noise_type: worse_label
  under_supported_classes: "3,5"
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 600
  epochs: 12
  learning_rate: 0.001
  weight_decay: 0.0001
  train_batch_size: 256
  mc_passes: 20

sweep_definitions:
  - parameter: aleatoric_noise_percentage
    value_type: float
    range:
      start: 0.0
      end: 0.5
      step: 0.1
```

## API Endpoints

### Create Batch Experiment
```
POST /api/v1/batch-experiments
```

### Get Batch Status
```
GET /api/v1/batch-experiments/{batch_id}
```

### List All Batches
```
GET /api/v1/batch-experiments
```

### Get Run Details
```
GET /api/v1/batch-experiments/{batch_id}/runs/{run_id}
```

## Database Schema

### BatchExperiment Table
- `id`: UUID
- `name`: Experiment name
- `description`: Optional description
- `method_type`: "attribution" or "benchmark"
- `base_config_yaml`: Base configuration
- `sweep_definitions_json`: Sweep parameters
- `status`: QUEUED, RUNNING, COMPLETED, FAILED
- `total_runs`: Number of sweep runs
- `completed_runs`: Completed count
- `failed_runs`: Failed count

### BatchExperimentRun Table
- `id`: UUID
- `batch_experiment_id`: Foreign key
- `run_index`: Sequential index
- `swept_parameter`: Parameter being swept
- `swept_value_numeric`: Numeric value
- `swept_value_text`: Text representation
- `resolved_config_yaml`: Full config for this run
- `aleatoric_auroc`: Result metric
- `epistemic_auroc`: Result metric
- `status`: Run status

## Future Enhancements

1. **Parallel Execution**: Run multiple experiments concurrently
2. **Result Visualization**: Built-in plotting endpoints
3. **Hyperparameter Optimization**: Automatic tuning
4. **Multi-Parameter Sweeps**: Grid search support
5. **Early Stopping**: Stop sweeps based on results