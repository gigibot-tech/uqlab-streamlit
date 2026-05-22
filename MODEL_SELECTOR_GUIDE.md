# 🎯 Model Selector Guide

## Overview

The **Model Selector** feature allows you to browse, load, and use trained models from completed experiments. This enables model reuse, comparison, and inference without retraining.

## Features

### 1. 📊 Browse Completed Experiments

- View all completed experiments with their performance metrics
- See AUROC scores for epistemic and aleatoric uncertainty detection
- Filter by model architecture, training parameters, and completion time
- Sort by performance or recency

### 2. 🔽 Load Model Checkpoints

Each saved checkpoint contains:
- **Full model object** (PyTorch model with trained weights)
- **Model state dict** (for flexible loading)
- **Training configuration** (architecture, hyperparameters)
- **Training metadata** (epochs, dataset config)

### 3. 🔮 Model Inference

Three inference modes:
- **Single Sample**: Upload an image for classification
- **Batch Inference**: Run predictions on evaluation dataset
- **Uncertainty Analysis**: View uncertainty signals and AUROC performance

## Usage

### Step 1: Navigate to Model Selector Tab

In the Streamlit app, click on the **"🎯 Model Selector"** tab.

### Step 2: Browse Experiments

The table shows:
- Experiment ID (short)
- Experiment name
- Completion timestamp
- Best epistemic AUROC
- Best aleatoric AUROC
- Model architecture
- Training epochs

### Step 3: Select and Load

1. Choose an experiment from the dropdown
2. Review configuration and performance in the expandable section
3. Click **"🔽 Load Model Checkpoint"**
4. Model is loaded into session state

### Step 4: Use Loaded Model

Once loaded, you can:
- View model architecture and configuration
- See uncertainty signal statistics
- Run inference (coming soon)
- Compare with other models

## Checkpoint Storage

Checkpoints are saved to:
```
/tmp/walaris_experiments/{experiment_id}/results/checkpoint.pt
```

Each checkpoint includes:
```python
{
    'model': model,  # Full PyTorch model
    'model_state_dict': model.state_dict(),
    'epoch': epochs,
    'config': {
        'hidden_dim': 256,
        'dropout': 0.2,
        'num_classes': 10,
        'dinov2_model': 'small'
    }
}
```

## Results Data

Additional results are saved to:
```
/tmp/walaris_experiments/{experiment_id}/results/results.pt
```

Contains:
- Model predictions and confidences
- Training embeddings and labels
- Evaluation embeddings and labels
- All 7 uncertainty signals
- AUROC results

## Session State

Loaded models are stored in Streamlit session state:
```python
st.session_state['loaded_model']  # PyTorch model
st.session_state['loaded_model_config']  # Configuration dict
st.session_state['loaded_model_experiment']  # Experiment metadata
```

## Example Workflow

### 1. Train Multiple Models

```python
# Run experiments with different configurations
# - Different epistemic strengths (under_train_per_class: 50, 100, 200)
# - Different aleatoric strengths (noise: 0%, 10%, 20%)
# - Different architectures (DINOv2 small, base, large)
```

### 2. Compare Performance

```python
# In Model Selector tab:
# - View all completed experiments
# - Sort by epistemic AUROC
# - Identify best performing model
```

### 3. Load Best Model

```python
# Select experiment with highest AUROC
# Load checkpoint
# View uncertainty signals
```

### 4. Use for Inference

```python
# Upload new images
# Get predictions + uncertainty scores
# Make decisions based on uncertainty
```

## API Integration

The model selector uses these API endpoints:

### Get Experiments
```http
GET /api/v1/experiments/no-auth
```

Returns list of all experiments with status and results.

### Load Checkpoint
```python
checkpoint = torch.load(
    f"/tmp/walaris_experiments/{experiment_id}/results/checkpoint.pt",
    map_location='cpu'
)
```

## Best Practices

### 1. Model Selection Criteria

Choose models based on:
- **Task requirements**: Epistemic vs aleatoric detection
- **Performance**: AUROC scores on validation set
- **Efficiency**: Model size and inference speed
- **Robustness**: Performance across different noise levels

### 2. Checkpoint Management

- Checkpoints are temporary (stored in `/tmp/`)
- Copy important checkpoints to permanent storage
- Document model configurations for reproducibility

### 3. Inference Considerations

- Use MC Dropout for uncertainty quantification
- Set appropriate number of forward passes (default: 20)
- Consider computational cost vs accuracy trade-off

## Future Enhancements

### Coming Soon

1. **Single Sample Inference**
   - Upload images directly in UI
   - Get predictions with uncertainty scores
   - Visualize attribution maps

2. **Batch Inference**
   - Run predictions on full datasets
   - Export results to CSV
   - Compare multiple models

3. **Model Comparison**
   - Side-by-side performance comparison
   - Statistical significance testing
   - Visualization of decision boundaries

4. **Model Export**
   - Export to ONNX format
   - Deploy to watsonx.ai
   - Create REST API endpoints

## Troubleshooting

### Checkpoint Not Found

**Problem**: `❌ Checkpoint not found at /tmp/walaris_experiments/{id}/results/checkpoint.pt`

**Solution**:
- Experiment may have been cleaned up
- Run a new experiment
- Check if experiment completed successfully

### Loading Error

**Problem**: `❌ Error loading checkpoint: ...`

**Solution**:
- Ensure PyTorch version compatibility
- Check if model dependencies are installed
- Verify checkpoint file is not corrupted

### No Completed Experiments

**Problem**: `📭 No completed experiments with saved models yet`

**Solution**:
- Run at least one experiment to completion
- Wait for experiments to finish (check status in other tabs)
- Ensure experiments completed without errors

## Technical Details

### Model Architecture

```python
class FeatureClassifier(nn.Module):
    def __init__(self, feature_dim, hidden_dim, num_classes, dropout):
        super().__init__()
        self.fc1 = nn.Linear(feature_dim, hidden_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(hidden_dim, num_classes)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        return self.fc2(x)
```

### Uncertainty Signals

7 signals computed for each sample:
1. **msp_uncertainty**: 1 - max softmax probability
2. **predictive_entropy**: Entropy of mean prediction
3. **mutual_info**: Mutual information (epistemic)
4. **inverse_coherence**: 1 - attribution coherence (aleatoric)
5. **dominance**: Attribution dominance (epistemic)
6. **inverse_mass**: 1 / attribution mass (epistemic)
7. **inverse_logit_magnitude**: 1 / logit L1 norm

### Performance Metrics

- **AUROC**: Area Under ROC Curve (0-1, higher is better)
- **Macro F1**: Balanced F1 score across all classes
- **Binary Classification**: One-vs-rest for epistemic/aleatoric

## References

- [DINOv2 Paper](https://arxiv.org/abs/2304.07193)
- [MC Dropout](https://arxiv.org/abs/1506.02142)
- [DualXDA Attribution](https://arxiv.org/abs/2303.04301)

---

**Made with Bob** 🤖