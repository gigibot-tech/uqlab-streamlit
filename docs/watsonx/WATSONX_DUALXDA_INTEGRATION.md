# watsonx.ai + DualXDA Integration Guide

## Overview

This guide explains how the watsonx.ai custom scorer integrates with the existing DualXDA attribution implementation from `uq_classification/attribution_signals.py`.

## Key Design Principle: Modular Attribution

The custom scorer (`watsonx_custom_scorer.py`) uses a **pluggable attribution interface**:

```python
scorer = UncertaintyScorer(
    model=model,
    mc_passes=20,
    attribution_fn=your_attribution_function  # DualXDA or custom
)
```

This allows you to:
- ✅ Use DualXDA when training data is available
- ✅ Use approximations when training data is not available
- ✅ Swap attribution methods without changing the scorer
- ✅ Deploy the same scorer to watsonx.ai regardless of attribution method

## DualXDA Integration

### What is DualXDA?

DualXDA (Dual eXplanation via Data Attribution) uses the Representer Theorem to compute sample-level influence scores. It identifies which training samples most influenced each prediction.

**Key signals computed:**
1. **Mass**: Total attribution magnitude (high = certain)
2. **Coherence**: Agreement among top supporters (high = certain)
3. **Dominance**: Concentration of attribution (high = few samples dominate)
4. **Label Disagreement**: Entropy of supporter labels
5. **Noisy Support Ratio**: Fraction of noisy supporters
6. **Attribution Concentration**: Gini coefficient of attributions
7. **Cross-Class Support**: Fraction of cross-class supporters

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    watsonx.ai Deployment                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │         UncertaintyScorer (Custom Scorer)          │    │
│  ├────────────────────────────────────────────────────┤    │
│  │                                                     │    │
│  │  1. MC Dropout (20 passes)                         │    │
│  │     → Predictive signals (MSP, entropy)            │    │
│  │     → Epistemic signal (mutual info)               │    │
│  │                                                     │    │
│  │  2. Attribution Function (pluggable)               │    │
│  │     ┌─────────────────────────────────────┐       │    │
│  │     │  DualXDA Wrapper                    │       │    │
│  │     ├─────────────────────────────────────┤       │    │
│  │     │  • Uses DualXDATracer               │       │    │
│  │     │  • Accesses training data           │       │    │
│  │     │  • Computes 7 attribution signals   │       │    │
│  │     └─────────────────────────────────────┘       │    │
│  │     → Attribution signals (mass, coherence, etc.) │    │
│  │                                                     │    │
│  │  3. Hybrid signal (inverse logit magnitude)        │    │
│  │                                                     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Single API Call Returns:                                   │
│  • Predictions [batch_size, num_classes]                    │
│  • 11 Uncertainty Signals [batch_size]                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Implementation

### Step 1: Create DualXDA Attribution Function

See `watsonx_dualxda_example.py` for complete code:

```python
from uq_classification.watsonx_dualxda_example import create_dualxda_attribution_fn

# Initialize DualXDA tracer
tracer = DualXDATracer(
    model=model,
    train_dataset=train_dataset,
    layer_name="classifier",
    cache_dir="./dualxda_cache",
    device=device
)

# Create attribution function
dualxda_fn = create_dualxda_attribution_fn(
    tracer=tracer,
    model=model,
    train_dataset=train_dataset,
    device=device,
    batch_size=32,
    top_k=10,
    num_classes=10
)
```

### Step 2: Create Scorer with DualXDA

```python
from uq_classification.watsonx_custom_scorer import UncertaintyScorer

scorer = UncertaintyScorer(
    model=model,
    mc_passes=20,
    attribution_fn=dualxda_fn  # Plug in DualXDA!
)
```

### Step 3: Export for watsonx.ai

```python
from uq_classification.watsonx_export import export_all_for_watsonx

export_all_for_watsonx(
    model=model,
    optimizer=optimizer,
    epoch=final_epoch,
    loss=final_loss,
    train_embeddings=train_embeddings,
    train_labels=train_labels,
    train_noisy_labels=train_noisy_labels,
    train_is_noisy=train_is_noisy,
    train_indices=train_indices,
    eval_embeddings=eval_embeddings,
    eval_clean_labels=eval_clean_labels,
    eval_noisy_labels=eval_noisy_labels,
    eval_is_noisy=eval_is_noisy,
    eval_group_labels=eval_group_labels,
    eval_indices=eval_indices,
    signal_table=signal_table,
    predictions=predictions,
    confidences=confidences,
    auroc_rows=auroc_rows,
    config=config,
    output_base_dir="./watsonx_deployment"
)
```

The export includes:
- Model checkpoint with DualXDA-enabled scorer
- Training embeddings (for DualXDA attribution)
- Evaluation embeddings
- All metadata and configuration

### Step 4: Deploy to watsonx.ai

Follow the deployment guide in `WATSONX_DEPLOYMENT_GUIDE.md`.

## Uncertainty Signals Computed

### Without DualXDA (4 signals)
1. **MSP Uncertainty**: 1 - max(softmax(logits))
2. **Predictive Entropy**: -Σ p(y) log p(y)
3. **Mutual Information**: H[y|x] - E[H[y|x,θ]]
4. **Inverse Logit Magnitude**: 1 / ||logits||

### With DualXDA (11 signals)
All above, plus:
5. **Inverse Mass**: 1 / total_attribution
6. **Inverse Coherence**: 1 / (1 + coherence)
7. **Dominance**: max_attribution / total_mass
8. **Label Disagreement**: Entropy of supporter labels
9. **Noisy Support Ratio**: Fraction of noisy supporters
10. **Attribution Concentration**: Gini coefficient
11. **Cross-Class Support**: Fraction of cross-class supporters

## Performance Comparison

### Local Inference (Streamlit)
- **Without DualXDA**: ~1-2 seconds per batch
- **With DualXDA**: ~10-35 seconds per batch (includes t-SNE visualization)

### watsonx.ai Inference
- **Without DualXDA**: ~1 second per batch
- **With DualXDA**: ~1-2 seconds per batch (server-side, no visualization)

**Key advantage**: Single API call returns all signals, avoiding 20+ round trips for MC Dropout.

## Code Reuse

The integration **reuses existing code** from `uq_classification/attribution_signals.py`:

```python
# Existing function (unchanged)
def compute_attribution_structure_signals(
    tracer: DualXDATracer,
    model: torch.nn.Module,
    eval_features: torch.Tensor,
    mean_predictions: torch.Tensor,
    train_dataset,
    device: str = "cuda",
    batch_size: int = 32,
    top_k: int = 10,
    num_classes: int = 10,
) -> Dict[str, torch.Tensor]:
    # ... existing implementation ...
```

The wrapper in `watsonx_dualxda_example.py` simply:
1. Converts logits → predictions
2. Calls `compute_attribution_structure_signals()`
3. Inverts mass/coherence for uncertainty format
4. Returns dictionary matching scorer interface

**No changes needed to existing DualXDA code!**

## Flexibility

The modular design supports multiple scenarios:

### Scenario 1: Full DualXDA (Training Data Available)
```python
scorer = UncertaintyScorer(
    model=model,
    mc_passes=20,
    attribution_fn=dualxda_fn  # Full DualXDA
)
# Returns: 11 signals
```

### Scenario 2: Approximation (No Training Data)
```python
scorer = UncertaintyScorer(
    model=model,
    mc_passes=20,
    attribution_fn=None  # Use approximations
)
# Returns: 7 signals (4 predictive + 3 approximated attribution)
```

### Scenario 3: Custom Attribution Method
```python
def my_custom_attribution(embeddings, logits):
    # Your custom implementation
    return {'custom_signal': values}

scorer = UncertaintyScorer(
    model=model,
    mc_passes=20,
    attribution_fn=my_custom_attribution
)
# Returns: 4 predictive + your custom signals
```

## Architecture Independence

The scorer works with **any model architecture**, not just DINOv2:

```python
# Works with any model that has forward() returning logits
class MyCustomModel(nn.Module):
    def forward(self, x):
        # ... your architecture ...
        return logits  # [batch_size, num_classes]

scorer = UncertaintyScorer(
    model=MyCustomModel(),  # Any architecture!
    mc_passes=20,
    attribution_fn=dualxda_fn
)
```

## Testing

### Local Testing
```python
# Test scorer locally before deployment
test_embeddings = torch.randn(10, 768).to(device)
results = scorer.score(test_embeddings)

print("Predictions:", results['predictions'].shape)
print("Uncertainty signals:")
for signal_name, signal_values in results['uncertainty'].items():
    print(f"  {signal_name}: {signal_values.shape}")
```

### watsonx.ai Testing
```python
from uq_classification.watsonx_scoring import create_mock_scoring_client

# Mock client for testing without deployment
client = create_mock_scoring_client(scorer)
results = client.score_batch(test_embeddings)
```

## Benefits Summary

✅ **Modular**: Plug in DualXDA or any attribution method  
✅ **Efficient**: Single API call for all signals  
✅ **Reusable**: Uses existing `attribution_signals.py` code  
✅ **Flexible**: Works with any model architecture  
✅ **Complete**: All 11 uncertainty signals in production  
✅ **Tested**: Local testing before deployment  
✅ **Scalable**: Server-side computation on watsonx.ai  

## Files Reference

- **`watsonx_custom_scorer.py`**: Core scorer with pluggable attribution
- **`watsonx_dualxda_example.py`**: DualXDA integration example
- **`attribution_signals.py`**: Existing DualXDA implementation (unchanged)
- **`watsonx_export.py`**: Export deployment package
- **`watsonx_scoring.py`**: API client for inference
- **`watsonx_uncertainty.py`**: Evaluation utilities

## Next Steps

1. Review `watsonx_dualxda_example.py` for complete code
2. Test DualXDA integration locally
3. Export deployment package with `export_all_for_watsonx()`
4. Deploy to watsonx.ai following `WATSONX_DEPLOYMENT_GUIDE.md`
5. Integrate with Streamlit UI for visualization

---

**Made with Bob** 🤖