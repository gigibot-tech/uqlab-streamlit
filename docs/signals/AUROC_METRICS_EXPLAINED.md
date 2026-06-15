# AUROC Metrics Explained: Understanding Uncertainty Quantification Results

## What is AUROC?

**AUROC (Area Under the Receiver Operating Characteristic Curve)** is a metric that measures how well a scoring system can distinguish between two classes. It ranges from 0 to 1, where:

- **1.0 = Perfect discrimination**: The model perfectly separates the two classes
- **0.5 = Random guessing**: No better than flipping a coin
- **0.0 = Perfect inverse**: The model consistently gets it backwards (rarely seen)

## In Our Uncertainty Quantification Context

### What We're Measuring

In our experiments, we use AUROC to evaluate how well **uncertainty signals** can identify problematic samples:

1. **Aleatoric Uncertainty (Data Noise)**: Can the signal detect samples with noisy/incorrect labels?
2. **Epistemic Uncertainty (Model Knowledge)**: Can the signal detect samples from under-supported classes?

### The "40% Aleatoric Noise" Question

When you see **"Aleatoric noise of 40%"**, this means:

- **40% of the training samples** from regular (well-supported) classes have **incorrect labels**
- These are intentionally mislabeled to simulate real-world label noise
- The remaining 60% have correct labels

**Example with 1000 samples:**
```
Regular classes (8 classes × 300 samples = 2400 samples):
├─ Clean: 2400 × 60% = 1,440 samples with correct labels
└─ Noisy: 2400 × 40% = 960 samples with wrong labels

Under-supported classes (2 classes × 50 samples = 100 samples):
└─ All clean (used to test epistemic uncertainty)
```

## Understanding AUROC Scores

### What Different Scores Mean

| AUROC Range | Interpretation | What It Means for Your Signal |
|-------------|----------------|-------------------------------|
| **0.90 - 1.00** | Excellent | Signal reliably identifies problematic samples |
| **0.80 - 0.90** | Good | Signal is useful but not perfect |
| **0.70 - 0.80** | Fair | Signal has some predictive power |
| **0.60 - 0.70** | Poor | Signal barely better than random |
| **0.50 - 0.60** | Very Poor | Almost no discriminative ability |
| **< 0.50** | Inverse | Signal might be inverted (higher scores = safer samples) |

### Your Results: 0.65 - 0.70 Range

If your signals consistently score **0.65 - 0.70**, this indicates:

✅ **Positive Interpretation:**
- The signals have **some ability** to detect problematic samples
- They're **better than random guessing** (0.5)
- There's a **weak but real correlation** between uncertainty and problems

⚠️ **Limitations:**
- The signals are **not strong enough** for reliable automated decisions
- You'd need to manually review ~40-50% of flagged samples
- The task might be **inherently difficult** with current features

### Why Might Scores Be "Stuck" at 0.65-0.70?

Several factors could explain consistently moderate AUROC scores:

1. **Feature Limitations**
   - DINOv2 embeddings might not capture the right information
   - The 768-dimensional space might not separate clean/noisy well
   - Need different feature extractors (e.g., ResNet, ViT variants)

2. **Label Noise Characteristics**
   - CIFAR-10N noise might be **adversarial** (hard to detect)
   - Noisy labels might look plausible to the model
   - Real-world noise patterns are complex

3. **Model Capacity**
   - Small MLP classifier might be too simple
   - Dropout-based uncertainty might not capture the right patterns
   - Need ensemble methods or Bayesian approaches

4. **Data Imbalance**
   - Under-supported classes have very few samples
   - Evaluation pools might be too small
   - Class distribution affects uncertainty estimates

## How AUROC is Calculated

### The Intuition

AUROC answers: **"If I pick a random positive sample and a random negative sample, what's the probability the positive has a higher score?"**

### Example Calculation

Suppose we have 5 samples with uncertainty scores:

| Sample | True Label | Uncertainty Score |
|--------|------------|-------------------|
| A | Noisy | 0.8 |
| B | Clean | 0.3 |
| C | Noisy | 0.7 |
| D | Clean | 0.4 |
| E | Noisy | 0.5 |

**Positive class = Noisy** (what we want to detect)

Compare all positive-negative pairs:
- A (0.8) vs B (0.3): ✅ Correct (0.8 > 0.3)
- A (0.8) vs D (0.4): ✅ Correct (0.8 > 0.4)
- C (0.7) vs B (0.3): ✅ Correct (0.7 > 0.3)
- C (0.7) vs D (0.4): ✅ Correct (0.7 > 0.4)
- E (0.5) vs B (0.3): ✅ Correct (0.5 > 0.3)
- E (0.5) vs D (0.4): ✅ Correct (0.5 > 0.4)

**AUROC = 6/6 = 1.0** (perfect!)

## Best Possible Outcomes

### Ideal Scenario (AUROC ≈ 0.95+)

```
Uncertainty Score Distribution:

Noisy Samples:     |████████████████|
                   |████████████████|
                   |████████████████|
                   0.7  0.8  0.9  1.0

Clean Samples: |████████████████|
               |████████████████|
               |████████████████|
               0.0  0.1  0.2  0.3

→ Clear separation, minimal overlap
```

### Your Scenario (AUROC ≈ 0.65-0.70)

```
Uncertainty Score Distribution:

Noisy Samples:  |████████████████████|
                |████████████████████|
                0.3  0.4  0.5  0.6  0.7

Clean Samples:  |████████████████████|
                |████████████████████|
                0.2  0.3  0.4  0.5  0.6

→ Significant overlap, weak separation
```

## Improving AUROC Scores

### Strategies to Try

1. **Better Feature Extraction**
   ```python
   # Try different backbones
   - ResNet-50 (untrained or pretrained)
   - ViT-Large
   - CLIP embeddings
   - Ensemble of multiple extractors
   ```

2. **Enhanced Uncertainty Estimation**
   ```python
   # Beyond MC Dropout
   - Deep Ensembles (train 5-10 models)
   - Bayesian Neural Networks
   - Temperature scaling
   - Evidential deep learning
   ```

3. **Better Training Strategies**
   ```python
   # Curriculum learning
   - Start with clean samples
   - Gradually introduce noise
   - Use confidence-based weighting
   ```

4. **Signal Combinations**
   ```python
   # Combine multiple signals
   - Predictive entropy + variance
   - Confidence + gradient norm
   - Train meta-classifier on all signals
   ```

## Interpreting Per-Signal Results

When you see results like:

```
Signal: predictive_entropy
├─ Aleatoric AUROC: 0.68
└─ Epistemic AUROC: 0.72

Signal: confidence_variance
├─ Aleatoric AUROC: 0.65
└─ Epistemic AUROC: 0.70
```

**This tells you:**
- `predictive_entropy` is slightly better at detecting both types of uncertainty
- Epistemic uncertainty (under-supported classes) is easier to detect than aleatoric (label noise)
- Both signals are weak but usable

## Practical Recommendations

### For AUROC 0.65-0.70 (Your Current Range)

**What you CAN do:**
- Use signals for **prioritizing manual review** (review high-uncertainty samples first)
- **Combine with other heuristics** (e.g., low confidence + high uncertainty)
- **Track trends** over training (uncertainty should decrease for clean samples)

**What you CANNOT do:**
- Automatically filter out noisy samples (too many false positives)
- Rely solely on uncertainty for critical decisions
- Expect consistent performance across different datasets

### When to Be Satisfied

- **Research/Exploration**: 0.65-0.70 is acceptable for understanding patterns
- **Production Systems**: Aim for 0.80+ for automated decisions
- **Safety-Critical**: Need 0.90+ with human oversight

## Next Steps

1. **Add untrained ResNet baseline** to see if features are the bottleneck
2. **Visualize uncertainty distributions** to understand overlap
3. **Try ensemble methods** for better uncertainty estimates
4. **Experiment with different noise types** (symmetric vs asymmetric)
5. **Increase evaluation pool sizes** for more stable AUROC estimates

---

## Quick Reference

**AUROC Cheat Sheet:**
- 1.0 = Perfect
- 0.9 = Excellent
- 0.8 = Good
- 0.7 = Fair
- 0.6 = Poor
- 0.5 = Random

**Your 0.65-0.70 scores mean:**
- ✅ Signals work, but weakly
- ⚠️ Not reliable for automation
- 🔍 Good for exploration and prioritization
- 🎯 Room for significant improvement
