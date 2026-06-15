# Uncertainty Metrics Explained: AUROC vs Raw Uncertainty Values

## The Key Distinction

You're seeing **TWO completely different types of metrics** in the validation plots:

### 1. AUROC Scores (0.0 to 1.0) ✅
**What it is**: A performance metric that measures how well an uncertainty signal can distinguish between problematic and clean samples.

**Range**: Always 0.0 to 1.0
- 1.0 = Perfect discrimination
- 0.5 = Random guessing
- 0.0 = Perfect inverse

**Where you see it**: 
- Top two rows of validation plots
- Signal performance evaluation
- Example: "Predictive Entropy AUROC = 0.68"

**What it measures**: "How good is this signal at detecting problems?"

---

### 2. Raw Uncertainty Values (Unbounded) ⚠️
**What it is**: The actual uncertainty measurements computed by the model.

**Range**: **Unbounded** - can be any positive number
- Entropy: typically 0 to log(num_classes) ≈ 2.3 for 10 classes
- Variance: can be 0.5, 1.5, 2.0, or higher
- No upper limit!

**Where you see it**:
- Bottom row (Row 3) of validation plots
- "mean_epistemic_uncertainty" and "mean_aleatoric_uncertainty"
- Example: "Mean epistemic uncertainty = 1.8"

**What it measures**: "How uncertain is the model about its predictions?"

---

## Why Raw Uncertainty Can Be > 1.0

### Entropy-Based Metrics
```python
# Predictive Entropy (Shannon Entropy)
predictive_entropy = -(mean_probs * log(mean_probs)).sum()

# For 10 classes (CIFAR-10):
# Maximum entropy = log(10) ≈ 2.30
# Typical range: 0.0 to 2.3
```

**Example values:**
- 0.0 = Completely certain (100% confidence in one class)
- 1.0 = Moderate uncertainty
- 2.3 = Maximum uncertainty (uniform distribution over 10 classes)

### Variance-Based Metrics
```python
# Variance of predictions across MC dropout passes
variance = predictions.var(dim=0)

# No theoretical upper bound!
# Can be 0.5, 1.5, 2.0, or even higher
```

**Example values:**
- 0.0 = All MC passes agree perfectly
- 0.5 = Low variance (consistent predictions)
- 1.5 = High variance (inconsistent predictions)
- 2.0+ = Very high variance (model is confused)

### Mutual Information (Epistemic Uncertainty)
```python
# Mutual Information: I(y;θ|x) = H(mean) - E[H(samples)]
mutual_info = predictive_entropy - expected_entropy

# Range: 0 to log(num_classes)
# For 10 classes: 0 to 2.3
```

---

## What the Plots Show

### Row 1 & 2: Signal Performance (AUROC)
```
📊 Epistemic AUROC: 0.68
📊 Aleatoric AUROC: 0.72
```
**Interpretation**: 
- These signals are **moderately good** at detecting problems
- Better than random (0.5) but not excellent (0.9+)
- The signal has **some discriminative power**

### Row 3: Raw Uncertainty Values
```
📈 Mean Epistemic Uncertainty: 1.8
📈 Mean Aleatoric Uncertainty: 0.9
```
**Interpretation**:
- The model has **high epistemic uncertainty** (1.8 out of max 2.3)
- The model has **moderate aleatoric uncertainty** (0.9)
- These are **absolute measurements**, not performance metrics

---

## Common Confusion Points

### ❌ WRONG: "Uncertainty should be 0-1 like AUROC"
**Why it's wrong**: Uncertainty is measured in different units depending on the metric:
- Entropy: 0 to log(num_classes)
- Variance: 0 to infinity
- Mutual Information: 0 to log(num_classes)

### ✅ CORRECT: "AUROC is 0-1, raw uncertainty is unbounded"
**Why it's right**: 
- AUROC is a **normalized performance metric**
- Raw uncertainty is a **measurement in its natural units**

---

## Practical Examples

### Example 1: High Uncertainty, Good AUROC
```
Mean Epistemic Uncertainty: 1.8  (high)
Epistemic AUROC: 0.85            (good)
```
**Interpretation**: 
- The model is very uncertain (1.8 is high)
- BUT the uncertainty signal is good at identifying problems (0.85 AUROC)
- **This is ideal!** High uncertainty on hard samples, low on easy ones

### Example 2: Low Uncertainty, Poor AUROC
```
Mean Epistemic Uncertainty: 0.3  (low)
Epistemic AUROC: 0.55            (poor)
```
**Interpretation**:
- The model is confident (0.3 is low)
- BUT the uncertainty signal doesn't distinguish problems well (0.55 ≈ random)
- **This is bad!** The model is overconfident

### Example 3: Your Current Results
```
Mean Epistemic Uncertainty: ~1.5  (moderate-high)
Epistemic AUROC: 0.68             (fair)
```
**Interpretation**:
- The model has moderate-high uncertainty
- The signal has some ability to detect problems
- **Room for improvement** in both metrics

---

## What Values to Expect

### Entropy-Based (Predictive Entropy, Mutual Info)
| Value | Interpretation | For 10 Classes |
|-------|----------------|----------------|
| 0.0 - 0.5 | Very confident | Low uncertainty |
| 0.5 - 1.0 | Confident | Moderate-low |
| 1.0 - 1.5 | Uncertain | Moderate |
| 1.5 - 2.0 | Very uncertain | Moderate-high |
| 2.0 - 2.3 | Maximally uncertain | High |

### Variance-Based
| Value | Interpretation |
|-------|----------------|
| 0.0 - 0.3 | Very consistent |
| 0.3 - 0.7 | Consistent |
| 0.7 - 1.2 | Inconsistent |
| 1.2 - 2.0 | Very inconsistent |
| 2.0+ | Extremely inconsistent |

---

## How to Read the Validation Plots

### Top Rows (AUROC): "How good is the signal?"
- **Y-axis**: 0.0 to 1.0 (performance metric)
- **Goal**: Higher is better (aim for 0.8+)
- **Interpretation**: Can this signal detect problems?

### Bottom Row (Raw Uncertainty): "How uncertain is the model?"
- **Y-axis**: Unbounded (measurement in natural units)
- **Goal**: Depends on context
  - **Epistemic**: Should decrease as dataset size increases
  - **Aleatoric**: Should increase as noise increases
- **Interpretation**: What's the absolute level of uncertainty?

---

## Key Takeaways

1. **AUROC (0-1)** measures **signal quality** - how well it detects problems
2. **Raw uncertainty (unbounded)** measures **model confidence** - how certain the model is
3. **Both are important** but measure different things
4. **Values > 1.0 are normal** for entropy and variance-based uncertainty
5. **Don't compare them directly** - they're in different units

---

## Quick Reference

| Metric | Range | What It Measures | Good Value |
|--------|-------|------------------|------------|
| **AUROC** | 0.0 - 1.0 | Signal performance | 0.8+ |
| **Predictive Entropy** | 0 - 2.3 | Model uncertainty | Depends on context |
| **Mutual Information** | 0 - 2.3 | Epistemic uncertainty | Should decrease with more data |
| **Variance** | 0 - ∞ | Prediction consistency | Lower is more confident |

---

*This explains why you see values like 1.5 or 2.0 in the uncertainty plots - they're measuring different things than AUROC!*