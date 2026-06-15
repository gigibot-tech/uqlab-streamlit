# Model-Agnostic Uncertainty Quantification Architecture

## Overview

This system provides a unified framework for uncertainty quantification across multiple neural network architectures. All architectures share a common interface and can be used interchangeably for attribution-based uncertainty estimation.

## Supported Architectures

### 1. DINOv2 + MLP (Feature Space)

**Use Case**: Transfer learning with frozen features

**Configuration**:
```yaml
model:
  architecture: dinov2_mlp
  training_mode: feature_space
  dinov2_model: small  # small, base, large, giant
  hidden_dim: 256
  dropout: 0.2
```

**Architecture Details**:
- **Input**: Pre-extracted DINOv2 embeddings (384-1536 dim depending on model size)
- **Backbone**: Frozen DINOv2 vision transformer
- **Classifier**: MLP with dropout
- **Feature Extraction**: From DINOv2 embeddings (already computed)

**Advantages**:
- Fast training (only MLP trained)
- Good performance with limited data
- Leverages powerful pretrained features
- Low memory footprint during training

**Disadvantages**:
- Requires feature extraction preprocessing step
- Cannot fine-tune backbone
- Fixed feature representation

**When to Use**:
- Limited computational resources
- Small datasets
- Quick experimentation
- Transfer learning scenarios

---

### 2. CNN MC Dropout (End-to-End)

**Use Case**: Lightweight end-to-end training

**Configuration**:
```yaml
model:
  architecture: cnn_mcdropout
  training_mode: end_to_end
  hidden_dim: 128
  dropout: 0.5
  num_conv_layers: 3
  conv_channels: [32, 64, 64]
```

**Architecture Details**:
- **Input**: Raw images (32×32×3 for CIFAR-10)
- **Backbone**: Custom CNN (Conv32→Conv64→Conv64)
- **Classifier**: FC layer with dropout
- **Feature Extraction**: From final FC layer (128-dim)

**Layer Structure**:
```
Input (32×32×3)
  ↓
Conv2d(3→32, 3×3) + ReLU + MaxPool
  ↓
Conv2d(32→64, 3×3) + ReLU + MaxPool
  ↓
Conv2d(64→64, 3×3) + ReLU + MaxPool
  ↓
Flatten
  ↓
Linear(64×4×4 → 128) + ReLU + Dropout(0.5)
  ↓
Linear(128 → num_classes)
```

**Advantages**:
- Simple, interpretable architecture
- Fast training and inference
- Low memory requirements
- Easy to debug

**Disadvantages**:
- Lower capacity than ResNet
- May underfit complex datasets
- Limited depth

**When to Use**:
- Simple datasets (CIFAR-10, MNIST)
- Baseline experiments
- Resource-constrained environments
- Educational purposes

---

### 3. ResNet18 MC Dropout (End-to-End)

**Use Case**: High-capacity end-to-end training

**Configuration**:
```yaml
model:
  architecture: resnet18_mcdropout
  training_mode: end_to_end
  hidden_dim: 512
  dropout: 0.3
  use_untrained_resnet: false  # true for random init
```

**Architecture Details**:
- **Input**: Raw images (32×32×3 for CIFAR-10)
- **Backbone**: ResNet18 (pretrained or random init)
- **Classifier**: FC layer with dropout
- **Feature Extraction**: From avgpool layer (512-dim)

**Layer Structure**:
```
Input (32×32×3)
  ↓
ResNet18 Backbone
  - Conv1 (7×7)
  - Layer1 (2 residual blocks)
  - Layer2 (2 residual blocks)
  - Layer3 (2 residual blocks)
  - Layer4 (2 residual blocks)
  - AvgPool
  ↓
Features (512-dim)
  ↓
Dropout(0.3)
  ↓
Linear(512 → num_classes)
```

**Advantages**:
- High capacity
- Strong performance
- Optional pretrained weights
- Residual connections help training

**Disadvantages**:
- Slower training
- More parameters (11M)
- Higher memory usage
- May overfit small datasets

**When to Use**:
- Complex datasets
- When accuracy is critical
- Sufficient computational resources
- Fine-tuning scenarios

---

## Common Interface

All architectures implement the same interface:

```python
class ModelInterface(nn.Module):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Standard forward pass.
        
        Args:
            x: Input tensor [B, ...] (images or features)
            
        Returns:
            logits: [B, num_classes]
        """
        
    def mc_forward(self, x: torch.Tensor, n_passes: int) -> torch.Tensor:
        """Monte Carlo forward with dropout enabled.
        
        Args:
            x: Input tensor [B, ...]
            n_passes: Number of MC passes
            
        Returns:
            probs: [n_passes, B, num_classes]
        """
        
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features for attribution.
        
        Args:
            x: Input tensor [B, ...]
            
        Returns:
            features: [B, feature_dim]
        """
```

---

## Feature Extraction for Attribution

All architectures extract features for DualXDA attribution:

### DINOv2 MLP
- **Source**: DINOv2 embeddings (already computed)
- **Dimension**: 384 (small), 768 (base), 1024 (large), 1536 (giant)
- **Location**: Input to MLP classifier

### CNN MC Dropout
- **Source**: Final FC layer before classifier
- **Dimension**: 128 (configurable via `hidden_dim`)
- **Location**: After last ReLU, before dropout

### ResNet18 MC Dropout
- **Source**: Global average pooling layer
- **Dimension**: 512 (fixed by ResNet18 architecture)
- **Location**: After avgpool, before classifier

---

## Attribution Signals

All architectures support DualXDA attribution with 7 signals:

1. **Gradient Norm**: ‖∇_x log p(y|x)‖
2. **Input × Gradient**: x ⊙ ∇_x log p(y|x)
3. **Integrated Gradients**: Path integral of gradients
4. **SmoothGrad**: Averaged gradients with noise
5. **GradCAM**: Class activation mapping
6. **Attention Rollout**: Attention-based attribution (DINOv2 only)
7. **Feature Variance**: Variance across MC passes

Each signal produces:
- **Aleatoric AUROC**: Detection of noisy labels
- **Epistemic AUROC**: Detection of under-supported classes

---

## Configuration Examples

### Example 1: DINOv2 Quick Experiment
```yaml
dataset:
  name: cifar10n
  noise_type: worse_label
  under_supported: "random:2"
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 100

model:
  architecture: dinov2_mlp
  training_mode: feature_space
  dinov2_model: small
  hidden_dim: 256
  dropout: 0.2

training:
  epochs: 12
  learning_rate: 0.001
  weight_decay: 0.0001
  batch_size: 256

evaluation:
  mc_passes: 20
```

### Example 2: CNN Baseline
```yaml
dataset:
  name: cifar10n
  noise_type: worse_label
  under_supported: "3,5"
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 600

model:
  architecture: cnn_mcdropout
  training_mode: end_to_end
  hidden_dim: 128
  dropout: 0.5
  num_conv_layers: 3
  conv_channels: [32, 64, 64]

training:
  epochs: 20
  learning_rate: 0.001
  weight_decay: 0.0001
  batch_size: 128

evaluation:
  mc_passes: 20
```

### Example 3: ResNet18 High Performance
```yaml
dataset:
  name: cifar10n
  noise_type: worse_label
  under_supported: "3,5"
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 600

model:
  architecture: resnet18_mcdropout
  training_mode: end_to_end
  hidden_dim: 512
  dropout: 0.3
  use_untrained_resnet: false  # Use pretrained weights

training:
  epochs: 15
  learning_rate: 0.0001  # Lower LR for fine-tuning
  weight_decay: 0.0001
  batch_size: 128

evaluation:
  mc_passes: 20
```

---

## Training Modes

### Feature Space Training
- **Applicable to**: DINOv2 MLP only
- **Process**: 
  1. Extract features once (offline)
  2. Train only MLP classifier
  3. Features cached for reuse
- **Speed**: Very fast (no backbone forward passes)

### End-to-End Training
- **Applicable to**: CNN, ResNet18
- **Process**:
  1. Train entire network from scratch or fine-tune
  2. Backprop through all layers
  3. Extract features during evaluation
- **Speed**: Slower but more flexible

---

## Performance Comparison

| Architecture | Params | Training Time | Inference Time | Typical Accuracy |
|-------------|--------|---------------|----------------|------------------|
| DINOv2 Small + MLP | 21M + 0.1M | Fast (5 min) | Fast | 85-90% |
| CNN MC Dropout | 0.5M | Medium (15 min) | Fast | 75-80% |
| ResNet18 MC Dropout | 11M | Slow (30 min) | Medium | 90-95% |

*Times are approximate for CIFAR-10 with 12 epochs on single GPU*

---

## Choosing an Architecture

### Use DINOv2 MLP when:
- ✅ You need fast experimentation
- ✅ You have limited compute
- ✅ Transfer learning is appropriate
- ✅ You want strong baseline performance

### Use CNN MC Dropout when:
- ✅ You need a simple baseline
- ✅ You want interpretable architecture
- ✅ You have very limited resources
- ✅ Dataset is relatively simple

### Use ResNet18 MC Dropout when:
- ✅ You need maximum accuracy
- ✅ You have sufficient compute
- ✅ Dataset is complex
- ✅ You want to fine-tune pretrained weights

---

## Implementation Details

### Model Factory
All models are created through `model_factory.py`:

```python
from uq_classification.model_factory import build_model

model = build_model(config)
```

### Feature Extractor
Features are extracted through `feature_extractor.py`:

```python
from uq_classification.feature_extractor import get_feature_extractor

extractor = get_feature_extractor(model, config)
features = extractor.extract_features(dataloader)
```

### Attribution Computer
Attribution is computed through `attribution_computer.py`:

```python
from uq_classification.attribution_computer import AttributionComputer

computer = AttributionComputer(model, config)
signals = computer.compute_all_signals(features, labels)
```

---

## Extension Points

### Adding a New Architecture

1. **Define Model Class** in `model_factory.py`:
```python
class MyCustomModel(nn.Module):
    def forward(self, x):
        # Your implementation
        
    def mc_forward(self, x, n_passes):
        # Your implementation
        
    def extract_features(self, x):
        # Your implementation
```

2. **Register in Factory**:
```python
def build_model(config):
    if config.architecture == "my_custom_model":
        return MyCustomModel(config)
```

3. **Add Feature Extractor**:
```python
class MyCustomFeatureExtractor(FeatureExtractor):
    def extract_features(self, dataloader):
        # Your implementation
```

4. **Update Config Schema**:
```python
architecture: Literal["dinov2_mlp", "cnn_mcdropout", "resnet18_mcdropout", "my_custom_model"]
```

---

## Best Practices

1. **Start Simple**: Begin with CNN or DINOv2 for quick validation
2. **Tune Dropout**: Higher dropout (0.5) for small models, lower (0.2-0.3) for large
3. **Adjust Learning Rate**: Lower LR (1e-4) for fine-tuning, higher (1e-3) for training from scratch
4. **Monitor Overfitting**: Use validation set, early stopping if needed
5. **Cache Features**: For DINOv2, extract features once and reuse
6. **MC Passes**: 20 passes is usually sufficient, more for critical applications

---

## Troubleshooting

### Poor Performance
- Try different architecture (ResNet18 for complex data)
- Increase model capacity (hidden_dim)
- Adjust learning rate
- Add data augmentation

### Overfitting
- Increase dropout
- Add weight decay
- Reduce model capacity
- Use more training data

### Slow Training
- Use DINOv2 feature space mode
- Reduce batch size
- Use smaller model (CNN)
- Enable mixed precision training

### Out of Memory
- Reduce batch size
- Use gradient accumulation
- Use smaller model
- Enable gradient checkpointing