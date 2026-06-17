# Examples

This directory contains example scripts demonstrating how to use the uncertainty quantification system.

## Available Examples

### 1. DINOv2 Training (`example_dinov2.py`)

Train a DINOv2-based classifier with MC Dropout.

**Features**:
- Feature space training (fast)
- Pre-extracted DINOv2 embeddings
- Attribution-based uncertainty signals

**Usage**:
```bash
cd uqlab-streamlit
python examples/example_dinov2.py
```

**Expected Output**:
- Training time: ~5 minutes
- Aleatoric AUROC: 0.85-0.90
- Epistemic AUROC: 0.90-0.95

---

### 2. CNN Training (`example_cnn.py`)

Train a simple CNN with MC Dropout.

**Features**:
- End-to-end training
- Lightweight architecture (~500K parameters)
- Fast training and inference

**Usage**:
```bash
cd uqlab-streamlit
python examples/example_cnn.py
```

**Expected Output**:
- Training time: ~15 minutes
- Aleatoric AUROC: 0.75-0.85
- Epistemic AUROC: 0.85-0.90

---

### 3. ResNet18 Training (`example_resnet.py`)

Train a ResNet18-based classifier with MC Dropout.

**Features**:
- End-to-end training
- High-capacity architecture (~11M parameters)
- Optional pretrained weights

**Usage**:
```bash
cd uqlab-streamlit
python examples/example_resnet.py
```

**Expected Output**:
- Training time: ~30 minutes
- Aleatoric AUROC: 0.85-0.92
- Epistemic AUROC: 0.90-0.95

---

### 4. Batch Experiment (`example_batch_sweep.py`)

Run a batch experiment with parameter sweep via API.

**Features**:
- Automated parameter sweep
- Multiple runs with different configurations
- Aggregated results analysis

**Setup**:
1. Start the FastAPI backend:
   ```bash
   cd uqlab-streamlit/backend
   uvicorn app.main:app --reload
   ```

2. Get API token:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "user@example.com", "password": "password"}'
   ```

3. Update token in script:
   ```python
   API_TOKEN = "your-actual-token-here"
   ```

**Usage**:
```bash
cd uqlab-streamlit
python examples/example_batch_sweep.py
```

**Expected Output**:
- Creates 6 runs (noise rates: 0.0, 0.1, 0.2, 0.3, 0.4, 0.5)
- Total time: ~30-60 minutes
- Results table with AUROC for each noise rate

---

## Quick Start

### Prerequisites

1. Install dependencies:
   ```bash
   cd uqlab-streamlit
   pip install -r requirements.txt
   ```

2. Download CIFAR-10N dataset:
   ```bash
   python scripts/download_cifar10n.py
   ```

3. (Optional) Extract DINOv2 features:
   ```bash
   python scripts/extract_dinov2_features.py
   ```

### Running Examples

All examples can be run directly:

```bash
# DINOv2 example
python examples/example_dinov2.py

# CNN example
python examples/example_cnn.py

# ResNet18 example
python examples/example_resnet.py

# Batch experiment (requires API)
python examples/example_batch_sweep.py
```

---

## Output Structure

Each example creates an output directory with:

```
/tmp/example_<architecture>_output/
├── results.json              # Main results file
├── model.pt                  # Trained model weights
├── attribution_signals.npz   # Attribution signals for all samples
├── config.yaml              # Full configuration used
├── training_log.txt         # Training logs
└── plots/                   # Visualization plots
    ├── auroc_curves.png
    ├── confusion_matrix.png
    └── uncertainty_distribution.png
```

---

## Customization

### Modify Configuration

Edit the config in each example script:

```python
config_content = """
dataset:
  name: cifar10n
  noise_type: worse_label  # Change noise type
  under_supported: "3,5"   # Change under-supported classes

model:
  architecture: dinov2_mlp
  hidden_dim: 256          # Adjust model capacity
  dropout: 0.2             # Adjust dropout rate

training:
  epochs: 12               # Adjust training duration
  learning_rate: 0.001     # Adjust learning rate
"""
```

### Add Custom Architecture

See `MIGRATION_GUIDE.md` for instructions on adding new architectures.

---

## Troubleshooting

### Issue: CUDA out of memory
**Solution**: Reduce batch size in config:
```yaml
training:
  batch_size: 64  # Reduce from 128 or 256
```

### Issue: DINOv2 features not found
**Solution**: Extract features first:
```bash
python scripts/extract_dinov2_features.py
```

### Issue: API connection refused
**Solution**: Start the backend:
```bash
cd backend
uvicorn app.main:app --reload
```

### Issue: Poor performance
**Solution**: Try different architecture or adjust hyperparameters:
- Increase `hidden_dim` for more capacity
- Adjust `dropout` (0.2-0.5)
- Increase `epochs` for longer training
- Try different `learning_rate` (1e-4 to 1e-3)

---

## Performance Comparison

| Example | Training Time | Parameters | Typical AUROC (Aleatoric) | Typical AUROC (Epistemic) |
|---------|--------------|------------|---------------------------|---------------------------|
| DINOv2  | ~5 min       | 21M + 0.1M | 0.85-0.90                | 0.90-0.95                |
| CNN     | ~15 min      | 0.5M       | 0.75-0.85                | 0.85-0.90                |
| ResNet18| ~30 min      | 11M        | 0.85-0.92                | 0.90-0.95                |

*Times are approximate for CIFAR-10 with default settings on single GPU*

---

## Next Steps

1. **Experiment with different architectures**: Try all three examples
2. **Run parameter sweeps**: Use batch experiment example
3. **Customize configurations**: Adjust hyperparameters for your use case
4. **Add new architectures**: Follow MIGRATION_GUIDE.md
5. **Integrate with API**: Use batch experiment for production workflows

---

## Additional Resources

- **Architecture Guide**: `../ARCHITECTURE_GUIDE.md`
- **Migration Guide**: `../MIGRATION_GUIDE.md`
- **API Documentation**: `../API_DOCUMENTATION.md`
- **Sweep Consolidation**: `../SWEEP_CONSOLIDATION.md`

---

## Support

For questions or issues:
1. Check the documentation files
2. Review example scripts
3. Check logs in output directories
4. Consult ARCHITECTURE_GUIDE.md for architecture details