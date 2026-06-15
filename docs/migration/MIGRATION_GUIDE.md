# Migration Guide: Adding New Architectures

This guide explains how to extend the system with new neural network architectures while maintaining compatibility with the unified uncertainty quantification framework.

## Overview

The system is designed to be model-agnostic. Any architecture can be integrated as long as it implements the standard interface for:
1. Forward pass (logits)
2. MC Dropout forward pass (probabilistic predictions)
3. Feature extraction (for attribution)

## Step-by-Step Integration

### Step 1: Define Model Class

Create your model class in `uq_classification/model_factory.py` implementing the required interface:

```python
import torch
import torch.nn as nn
from typing import Tuple

class MyCustomModel(nn.Module):
    """Custom model with MC Dropout support.
    
    Args:
        num_classes: Number of output classes
        hidden_dim: Hidden layer dimension
        dropout: Dropout probability
        **kwargs: Additional model-specific parameters
    """
    
    def __init__(
        self,
        num_classes: int = 10,
        hidden_dim: int = 256,
        dropout: float = 0.3,
        **kwargs
    ):
        super().__init__()
        
        # Define your architecture
        self.backbone = self._build_backbone(**kwargs)
        self.feature_dim = hidden_dim
        
        # Classifier with dropout
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_dim, num_classes)
        
    def _build_backbone(self, **kwargs):
        """Build the backbone network."""
        # Your backbone implementation
        return nn.Sequential(
            # Your layers here
        )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Standard forward pass.
        
        Args:
            x: Input tensor [B, C, H, W] or [B, D]
            
        Returns:
            logits: [B, num_classes]
        """
        features = self.backbone(x)
        features = self.dropout(features)
        logits = self.classifier(features)
        return logits
    
    def mc_forward(self, x: torch.Tensor, n_passes: int = 20) -> torch.Tensor:
        """Monte Carlo forward with dropout enabled.
        
        Args:
            x: Input tensor [B, ...]
            n_passes: Number of MC passes
            
        Returns:
            probs: [n_passes, B, num_classes]
        """
        self.train()  # Enable dropout
        
        predictions = []
        with torch.no_grad():
            for _ in range(n_passes):
                logits = self.forward(x)
                probs = torch.softmax(logits, dim=-1)
                predictions.append(probs)
        
        return torch.stack(predictions)
    
    def extract_features(self, x: torch.Tensor) -> torch.Tensor:
        """Extract features for attribution.
        
        Args:
            x: Input tensor [B, ...]
            
        Returns:
            features: [B, feature_dim]
        """
        return self.backbone(x)
```

### Step 2: Register in Model Factory

Add your model to the `build_model()` function in `model_factory.py`:

```python
def build_model(config: ModelConfig) -> nn.Module:
    """Build model based on configuration.
    
    Args:
        config: Model configuration
        
    Returns:
        Initialized model
    """
    if config.architecture == "dinov2_mlp":
        return DINOv2MLP(...)
    elif config.architecture == "cnn_mcdropout":
        return CNNMCDropout(...)
    elif config.architecture == "resnet18_mcdropout":
        return ResNet18MCDropout(...)
    elif config.architecture == "my_custom_model":
        return MyCustomModel(
            num_classes=config.num_classes,
            hidden_dim=config.hidden_dim,
            dropout=config.dropout,
            # Add any custom parameters from config
        )
    else:
        raise ValueError(f"Unknown architecture: {config.architecture}")
```

### Step 3: Add Feature Extractor

Create a feature extractor in `uq_classification/feature_extractor.py`:

```python
class MyCustomFeatureExtractor(FeatureExtractor):
    """Feature extractor for MyCustomModel."""
    
    def __init__(self, model: nn.Module, config: Config):
        super().__init__(model, config)
        self.feature_dim = model.feature_dim
    
    def extract_features(
        self, 
        dataloader: DataLoader
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Extract features from data.
        
        Args:
            dataloader: Data loader
            
        Returns:
            features: [N, feature_dim]
            labels: [N]
        """
        self.model.eval()
        all_features = []
        all_labels = []
        
        with torch.no_grad():
            for batch in dataloader:
                images, labels = batch
                images = images.to(self.device)
                
                # Extract features using model's method
                features = self.model.extract_features(images)
                
                all_features.append(features.cpu())
                all_labels.append(labels)
        
        features = torch.cat(all_features, dim=0)
        labels = torch.cat(all_labels, dim=0)
        
        return features, labels
    
    def get_feature_dim(self) -> int:
        """Get feature dimension."""
        return self.feature_dim
```

Register it in `get_feature_extractor()`:

```python
def get_feature_extractor(
    model: nn.Module,
    config: Config
) -> FeatureExtractor:
    """Get appropriate feature extractor for model."""
    
    if config.architecture == "dinov2_mlp":
        return DINOv2FeatureExtractor(model, config)
    elif config.architecture == "cnn_mcdropout":
        return CNNFeatureExtractor(model, config)
    elif config.architecture == "resnet18_mcdropout":
        return ResNet18FeatureExtractor(model, config)
    elif config.architecture == "my_custom_model":
        return MyCustomFeatureExtractor(model, config)
    else:
        raise ValueError(f"Unknown architecture: {config.architecture}")
```

### Step 4: Update Configuration Schema

Add your architecture to the config in `uq_classification/config.py`:

```python
from typing import Literal

class ModelConfig(BaseModel):
    """Model configuration."""
    
    architecture: Literal[
        "dinov2_mlp",
        "cnn_mcdropout", 
        "resnet18_mcdropout",
        "my_custom_model"  # Add your architecture
    ]
    training_mode: Literal["feature_space", "end_to_end"]
    
    # Common parameters
    hidden_dim: int = 256
    dropout: float = 0.3
    
    # Add custom parameters for your model
    my_custom_param: int = 128
    another_param: str = "default"
```

### Step 5: Create Test Configuration

Create a test config in `configs/test/`:

```yaml
# configs/test/test_my_custom_model.yaml
dataset:
  name: cifar10n
  noise_type: worse_label
  under_supported: "random:2"
  under_train_per_class: 50
  regular_train_per_class: 300
  eval_per_group: 100

model:
  architecture: my_custom_model
  training_mode: end_to_end
  hidden_dim: 256
  dropout: 0.3
  my_custom_param: 128
  another_param: "test_value"

training:
  epochs: 5
  learning_rate: 0.001
  weight_decay: 0.0001
  batch_size: 128

evaluation:
  mc_passes: 10
```

### Step 6: Test Your Implementation

Run the validation script:

```bash
cd walaris-cen
python scripts/run_fast_uncertainty_classification.py \
    configs/test/test_my_custom_model.yaml \
    /tmp/test_my_custom_model
```

Verify:
- ✅ Model trains without errors
- ✅ MC forward pass works
- ✅ Features are extracted correctly
- ✅ Attribution signals are computed
- ✅ Results are saved properly

## Advanced Integration

### Custom Training Loop

If your model requires a custom training procedure:

```python
class MyCustomTrainer:
    """Custom trainer for special training requirements."""
    
    def __init__(self, model, config):
        self.model = model
        self.config = config
        
    def train_epoch(self, dataloader, optimizer):
        """Custom training epoch."""
        self.model.train()
        
        for batch in dataloader:
            # Your custom training logic
            pass
```

Register in `train_model()` function:

```python
def train_model(model, config, train_loader, val_loader):
    if config.architecture == "my_custom_model":
        trainer = MyCustomTrainer(model, config)
        return trainer.train(train_loader, val_loader)
    else:
        # Standard training
        return standard_train(model, config, train_loader, val_loader)
```

### Custom Attribution Methods

If your model supports special attribution methods:

```python
class MyCustomAttributionComputer(AttributionComputer):
    """Custom attribution for special model features."""
    
    def compute_custom_signal(self, features, labels):
        """Compute model-specific attribution signal."""
        # Your implementation
        pass
```

### Multi-Modal Models

For models with multiple input types:

```python
class MultiModalModel(nn.Module):
    def forward(self, images, text):
        """Forward with multiple inputs."""
        image_features = self.image_encoder(images)
        text_features = self.text_encoder(text)
        combined = torch.cat([image_features, text_features], dim=-1)
        return self.classifier(combined)
    
    def extract_features(self, images, text):
        """Extract combined features."""
        image_features = self.image_encoder(images)
        text_features = self.text_encoder(text)
        return torch.cat([image_features, text_features], dim=-1)
```

## Common Patterns

### Pattern 1: Pretrained Backbone

```python
class PretrainedModel(nn.Module):
    def __init__(self, backbone_name: str, num_classes: int, dropout: float):
        super().__init__()
        
        # Load pretrained backbone
        self.backbone = timm.create_model(
            backbone_name,
            pretrained=True,
            num_classes=0  # Remove classifier
        )
        
        # Get feature dimension
        self.feature_dim = self.backbone.num_features
        
        # Add custom classifier
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.feature_dim, num_classes)
```

### Pattern 2: Frozen Features

```python
class FrozenFeatureModel(nn.Module):
    def __init__(self, feature_extractor, num_classes: int, dropout: float):
        super().__init__()
        
        # Freeze feature extractor
        self.feature_extractor = feature_extractor
        for param in self.feature_extractor.parameters():
            param.requires_grad = False
        
        # Trainable classifier
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(feature_dim, num_classes)
```

### Pattern 3: Ensemble Model

```python
class EnsembleModel(nn.Module):
    def __init__(self, models: List[nn.Module]):
        super().__init__()
        self.models = nn.ModuleList(models)
    
    def forward(self, x):
        """Average predictions from all models."""
        logits = [model(x) for model in self.models]
        return torch.stack(logits).mean(dim=0)
    
    def mc_forward(self, x, n_passes):
        """MC forward for ensemble."""
        all_predictions = []
        for model in self.models:
            preds = model.mc_forward(x, n_passes)
            all_predictions.append(preds)
        return torch.cat(all_predictions, dim=0)
```

## Validation Checklist

Before submitting your new architecture:

- [ ] Model implements `forward()`, `mc_forward()`, `extract_features()`
- [ ] Feature extractor works correctly
- [ ] Configuration schema updated
- [ ] Test config created
- [ ] Model trains successfully
- [ ] MC Dropout produces varied predictions
- [ ] Features have correct dimensions
- [ ] Attribution signals compute without errors
- [ ] Results match expected format
- [ ] Documentation added to ARCHITECTURE_GUIDE.md
- [ ] Example added to examples/ directory

## Troubleshooting

### Issue: Features have wrong dimensions
**Solution**: Check `extract_features()` output shape matches `feature_dim`

### Issue: MC forward gives identical predictions
**Solution**: Ensure dropout is enabled with `self.train()` in `mc_forward()`

### Issue: Attribution fails
**Solution**: Verify features are differentiable and gradients flow correctly

### Issue: Out of memory
**Solution**: Reduce batch size or implement gradient checkpointing

### Issue: Poor performance
**Solution**: Check learning rate, dropout rate, and model capacity

## Examples

See the `examples/` directory for complete implementations:
- `examples/example_dinov2.py` - DINOv2 integration
- `examples/example_cnn.py` - CNN integration
- `examples/example_resnet.py` - ResNet integration
- `examples/example_custom.py` - Custom model template

## Support

For questions or issues:
1. Check existing architectures in `model_factory.py`
2. Review ARCHITECTURE_GUIDE.md
3. Run validation script with debug mode
4. Check logs in output directory

## Best Practices

1. **Keep it Simple**: Start with minimal implementation
2. **Test Early**: Validate each component separately
3. **Document**: Add docstrings and comments
4. **Follow Patterns**: Use existing models as templates
5. **Validate**: Run full test suite before integration
6. **Optimize Later**: Get it working first, then optimize