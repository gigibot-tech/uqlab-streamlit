# API Documentation

Complete reference for the Uncertainty Quantification FastAPI backend.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require authentication via JWT tokens (except login/register).

```http
Authorization: Bearer <token>
```

---

## Table of Contents

1. [Authentication](#authentication-endpoints)
2. [Datasets](#dataset-endpoints)
3. [Single Experiments](#single-experiment-endpoints)
4. [Batch Experiments](#batch-experiment-endpoints)
5. [UQ Benchmarks](#uq-benchmark-endpoints)
6. [Users](#user-endpoints)

---

## Authentication Endpoints

### POST /auth/login

Login and receive JWT token.

**Request**:
```json
{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### POST /auth/register

Register new user.

**Request**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

**Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true
}
```

---

## Dataset Endpoints

### GET /datasets

List available datasets.

**Response**:
```json
{
  "datasets": [
    {
      "name": "cifar10n",
      "description": "CIFAR-10 with noisy labels",
      "noise_types": ["clean", "worse_label", "aggre_label", "random_label1", "random_label2", "random_label3"],
      "num_classes": 10,
      "train_size": 50000,
      "test_size": 10000
    }
  ]
}
```

### GET /datasets/{dataset_name}/info

Get detailed dataset information.

**Response**:
```json
{
  "name": "cifar10n",
  "description": "CIFAR-10 with noisy labels",
  "noise_types": ["clean", "worse_label", ...],
  "num_classes": 10,
  "class_names": ["airplane", "automobile", ...],
  "train_size": 50000,
  "test_size": 10000,
  "image_shape": [32, 32, 3]
}
```

---

## Single Experiment Endpoints

### POST /experiments

Create and run a single experiment.

**Request**:
```json
{
  "name": "DINOv2 Baseline",
  "config": {
    "noise_type": "worse_label",
    "aleatoric_noise_percentage": 0.0,
    "under_supported_classes": "3,5",
    "under_train_per_class": 50,
    "regular_train_per_class": 300,
    "eval_per_group": 600,
    "architecture": "dinov2_mlp",
    "training_mode": "feature_space",
    "dinov2_model": "small",
    "hidden_dim": 256,
    "dropout": 0.2,
    "epochs": 12,
    "learning_rate": 0.001,
    "weight_decay": 0.0001,
    "train_batch_size": 256,
    "mc_passes": 20
  }
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "DINOv2 Baseline",
  "status": "queued",
  "progress": 0.0,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET /experiments/{experiment_id}

Get experiment status and results.

**Response**:
```json
{
  "id": "uuid",
  "name": "DINOv2 Baseline",
  "status": "completed",
  "progress": 100.0,
  "aleatoric_auroc": 0.85,
  "epistemic_auroc": 0.92,
  "best_signals": {
    "aleatoric": [
      {
        "signal_name": "gradient_norm",
        "auroc": 0.85,
        "threshold": 0.5
      }
    ],
    "epistemic": [
      {
        "signal_name": "feature_variance",
        "auroc": 0.92,
        "threshold": 0.3
      }
    ]
  },
  "results_path": "/path/to/results",
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:15:00Z"
}
```

### GET /experiments

List all experiments for current user.

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `status`: str (optional filter)

**Response**:
```json
{
  "experiments": [
    {
      "id": "uuid",
      "name": "DINOv2 Baseline",
      "status": "completed",
      "aleatoric_auroc": 0.85,
      "epistemic_auroc": 0.92,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### DELETE /experiments/{experiment_id}

Delete an experiment.

**Response**:
```json
{
  "message": "Experiment deleted successfully"
}
```

---

## Batch Experiment Endpoints

### POST /batch-experiments

Create a batch experiment with parameter sweep.

**Request**:
```json
{
  "name": "Noise Rate Sweep",
  "description": "Sweep noise rates from 0% to 50%",
  "method_type": "attribution",
  "base_config": {
    "architecture": "dinov2_mlp",
    "training_mode": "feature_space",
    "dinov2_model": "small",
    "hidden_dim": 256,
    "dropout": 0.2,
    "noise_type": "worse_label",
    "under_supported_classes": "3,5",
    "under_train_per_class": 50,
    "regular_train_per_class": 300,
    "eval_per_group": 600,
    "epochs": 12,
    "learning_rate": 0.001,
    "weight_decay": 0.0001,
    "train_batch_size": 256,
    "mc_passes": 20
  },
  "sweep_definitions": [
    {
      "parameter": "aleatoric_noise_percentage",
      "value_type": "float",
      "range": {
        "start": 0.0,
        "end": 0.5,
        "step": 0.1
      }
    }
  ],
  "execution_mode": "sequential"
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "Noise Rate Sweep",
  "status": "queued",
  "total_runs": 6,
  "completed_runs": 0,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET /batch-experiments/{batch_id}

Get batch experiment status.

**Response**:
```json
{
  "id": "uuid",
  "name": "Noise Rate Sweep",
  "description": "Sweep noise rates from 0% to 50%",
  "method_type": "attribution",
  "status": "running",
  "progress": 50.0,
  "total_runs": 6,
  "completed_runs": 3,
  "failed_runs": 0,
  "successful_runs": 3,
  "current_run_index": 3,
  "created_at": "2024-01-01T00:00:00Z",
  "started_at": "2024-01-01T00:01:00Z"
}
```

### GET /batch-experiments/{batch_id}/runs

Get all runs in a batch.

**Response**:
```json
{
  "runs": [
    {
      "id": "uuid",
      "run_index": 0,
      "run_name": "noise_0.0",
      "status": "completed",
      "swept_parameter": "aleatoric_noise_percentage",
      "swept_value_numeric": 0.0,
      "aleatoric_auroc": 0.85,
      "epistemic_auroc": 0.92,
      "created_at": "2024-01-01T00:01:00Z",
      "completed_at": "2024-01-01T00:05:00Z"
    },
    {
      "id": "uuid",
      "run_index": 1,
      "run_name": "noise_0.1",
      "status": "completed",
      "swept_parameter": "aleatoric_noise_percentage",
      "swept_value_numeric": 0.1,
      "aleatoric_auroc": 0.82,
      "epistemic_auroc": 0.90,
      "created_at": "2024-01-01T00:05:00Z",
      "completed_at": "2024-01-01T00:09:00Z"
    }
  ],
  "total": 6
}
```

### GET /batch-experiments/{batch_id}/runs/{run_id}

Get detailed run information.

**Response**:
```json
{
  "id": "uuid",
  "run_index": 0,
  "run_name": "noise_0.0",
  "status": "completed",
  "swept_parameter": "aleatoric_noise_percentage",
  "swept_value_numeric": 0.0,
  "swept_value_text": "0.0",
  "aleatoric_auroc": 0.85,
  "epistemic_auroc": 0.92,
  "train_size": 3050,
  "eval_sizes": {
    "under_supported": 200,
    "regular": 1200,
    "aleatoric_noise": 0
  },
  "result_summary": {
    "best_aleatoric_signal": "gradient_norm",
    "best_epistemic_signal": "feature_variance"
  },
  "output_dir": "/path/to/output",
  "created_at": "2024-01-01T00:01:00Z",
  "completed_at": "2024-01-01T00:05:00Z"
}
```

### GET /batch-experiments

List all batch experiments.

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `status`: str (optional filter)
- `method_type`: str (optional filter: "attribution" or "benchmark")

**Response**:
```json
{
  "batch_experiments": [
    {
      "id": "uuid",
      "name": "Noise Rate Sweep",
      "method_type": "attribution",
      "status": "completed",
      "total_runs": 6,
      "completed_runs": 6,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### GET /batch-experiments/{batch_id}/results/summary

Get aggregated results summary.

**Response**:
```json
{
  "batch_id": "uuid",
  "name": "Noise Rate Sweep",
  "swept_parameter": "aleatoric_noise_percentage",
  "results": [
    {
      "parameter_value": 0.0,
      "aleatoric_auroc": 0.85,
      "epistemic_auroc": 0.92
    },
    {
      "parameter_value": 0.1,
      "aleatoric_auroc": 0.82,
      "epistemic_auroc": 0.90
    }
  ],
  "statistics": {
    "mean_aleatoric_auroc": 0.835,
    "std_aleatoric_auroc": 0.015,
    "mean_epistemic_auroc": 0.91,
    "std_epistemic_auroc": 0.01
  }
}
```

### DELETE /batch-experiments/{batch_id}

Delete a batch experiment and all its runs.

**Response**:
```json
{
  "message": "Batch experiment deleted successfully"
}
```

---

## UQ Benchmark Endpoints

### POST /uq-benchmarks/results

Create a benchmark result.

**Request**:
```json
{
  "method": "gaussian_logits",
  "framework": "pytorch",
  "dataset_config": {
    "name": "cifar10n",
    "noise_type": "worse_label",
    "train_size": 3050
  },
  "training_config": {
    "epochs": 12,
    "learning_rate": 0.001,
    "batch_size": 128
  },
  "evaluation_config": {
    "mc_passes": 20
  },
  "accuracy": 0.85,
  "aleatoric_uncertainty": 0.15,
  "epistemic_uncertainty": 0.08,
  "training_time": 300.5,
  "evaluation_time": 45.2
}
```

**Response**:
```json
{
  "id": "uuid",
  "method": "gaussian_logits",
  "framework": "pytorch",
  "accuracy": 0.85,
  "aleatoric_uncertainty": 0.15,
  "epistemic_uncertainty": 0.08,
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET /uq-benchmarks/results/{result_id}

Get benchmark result details.

**Response**:
```json
{
  "id": "uuid",
  "method": "gaussian_logits",
  "framework": "pytorch",
  "dataset_config": {...},
  "training_config": {...},
  "evaluation_config": {...},
  "accuracy": 0.85,
  "aleatoric_uncertainty": 0.15,
  "epistemic_uncertainty": 0.08,
  "training_time": 300.5,
  "evaluation_time": 45.2,
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET /uq-benchmarks/results

List benchmark results.

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `method`: str (optional filter)
- `framework`: str (optional filter)

**Response**:
```json
{
  "results": [
    {
      "id": "uuid",
      "method": "gaussian_logits",
      "framework": "pytorch",
      "accuracy": 0.85,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /uq-benchmarks/sweeps

Create a benchmark sweep.

**Request**:
```json
{
  "name": "Gaussian Logits Noise Sweep",
  "description": "Sweep noise rates",
  "method": "gaussian_logits",
  "sweep_parameter": "noise_rate",
  "sweep_values": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
  "base_config": {
    "framework": "pytorch",
    "dataset": "cifar10n",
    "epochs": 12,
    "learning_rate": 0.001
  }
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "Gaussian Logits Noise Sweep",
  "method": "gaussian_logits",
  "status": "queued",
  "total_runs": 6,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET /uq-benchmarks/sweeps/{sweep_id}

Get sweep status and results.

**Response**:
```json
{
  "id": "uuid",
  "name": "Gaussian Logits Noise Sweep",
  "method": "gaussian_logits",
  "sweep_parameter": "noise_rate",
  "status": "completed",
  "total_runs": 6,
  "completed_runs": 6,
  "failed_runs": 0,
  "results": [
    {
      "parameter_value": 0.0,
      "accuracy": 0.85,
      "aleatoric_uncertainty": 0.15
    }
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:30:00Z"
}
```

---

## User Endpoints

### GET /users/me

Get current user information.

**Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false
}
```

### PATCH /users/me

Update current user information.

**Request**:
```json
{
  "full_name": "Jane Doe",
  "email": "jane@example.com"
}
```

**Response**:
```json
{
  "id": "uuid",
  "email": "jane@example.com",
  "full_name": "Jane Doe",
  "is_active": true
}
```

### PATCH /users/me/password

Change password.

**Request**:
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

**Response**:
```json
{
  "message": "Password updated successfully"
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid configuration: missing required field 'architecture'"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Experiment not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "config", "epochs"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

- **Authentication endpoints**: 5 requests per minute
- **Experiment creation**: 10 requests per minute
- **Other endpoints**: 100 requests per minute

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum items to return (default: 100, max: 1000)

**Response includes**:
```json
{
  "items": [...],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

---

## WebSocket Support

Real-time experiment updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/experiments/{experiment_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Progress:', data.progress);
  console.log('Status:', data.status);
};
```

**Message Format**:
```json
{
  "type": "progress_update",
  "experiment_id": "uuid",
  "status": "running",
  "progress": 45.5,
  "message": "Training epoch 5/12"
}
```

---

## SDK Examples

### Python SDK

```python
from uqlab_client import UQLabClient

client = UQLabClient(
    base_url="http://localhost:8000",
    token="your-jwt-token"
)

# Create experiment
experiment = client.experiments.create(
    name="My Experiment",
    config={
        "architecture": "dinov2_mlp",
        "epochs": 12,
        ...
    }
)

# Wait for completion
result = client.experiments.wait_for_completion(experiment.id)
print(f"Aleatoric AUROC: {result.aleatoric_auroc}")
```

### JavaScript SDK

```javascript
import { UQLabClient } from '@uqlab/client';

const client = new UQLabClient({
  baseUrl: 'http://localhost:8000',
  token: 'your-jwt-token'
});

// Create experiment
const experiment = await client.experiments.create({
  name: 'My Experiment',
  config: {
    architecture: 'dinov2_mlp',
    epochs: 12,
    ...
  }
});

// Poll for results
const result = await client.experiments.waitForCompletion(experiment.id);
console.log(`Aleatoric AUROC: ${result.aleatoric_auroc}`);
```

---

## OpenAPI Specification

Full OpenAPI 3.0 specification available at:
```
http://localhost:8000/api/v1/openapi.json
```

Interactive documentation:
```
http://localhost:8000/docs
```

Alternative documentation:
```
http://localhost:8000/redoc