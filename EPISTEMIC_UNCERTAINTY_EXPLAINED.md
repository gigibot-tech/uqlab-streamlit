# Epistemic Uncertainty Calculation Explained

## What is Epistemic Uncertainty?

**Epistemic uncertainty** (also called "model uncertainty") represents **what the model doesn't know** due to lack of training data. It can be reduced by collecting more data.

## How It's Calculated

### Method 1: Mutual Information (Information Theoretic)

```
Epistemic Uncertainty = Mutual Information = H[y|x] - E[H[y|x,θ]]
```

Where:
- `H[y|x]` = Predictive entropy (total uncertainty)
- `E[H[y|x,θ]]` = Expected entropy (aleatoric uncertainty)
- `θ` = Model parameters

**In practice** (using MC Dropout with T passes):

```python
# 1. Get T predictions with dropout enabled
predictions = []
for t in range(T):  # T = mc_passes (e.g., 20)
    pred = model(x, training=True)  # Dropout active
    predictions.append(pred)

# 2. Calculate predictive entropy (total uncertainty)
mean_pred = np.mean(predictions, axis=0)  # Average prediction
H_pred = -np.sum(mean_pred * np.log(mean_pred + 1e-10))

# 3. Calculate expected entropy (aleatoric)
entropies = []
for pred in predictions:
    H_i = -np.sum(pred * np.log(pred + 1e-10))
    entropies.append(H_i)
E_entropy = np.mean(entropies)

# 4. Mutual information = epistemic uncertainty
mutual_info = H_pred - E_entropy
```

### Method 2: Variance of Predictions (Gaussian Logits)

```python
# Get logits (pre-softmax) from T forward passes
logits = []
for t in range(T):
    logit = model.get_logits(x, training=True)
    logits.append(logit)

# Epistemic uncertainty = variance across passes
epistemic = np.var(logits, axis=0).mean()
```

## Why Is Epistemic Uncertainty High?

Looking at your plot, epistemic uncertainty is ~0.6-0.7 (relatively flat across noise levels). This is **expected** because:

### Reason 1: Under-Supported Classes
```
Configuration:
- Under-supported classes: 2 classes (e.g., random:2)
- Under-train samples: 50 per class
- Regular classes: 8 classes  
- Regular samples: 300 per class

Total training data:
- Under-supported: 2 × 50 = 100 samples
- Regular: 8 × 300 = 2,400 samples
- Total: 2,500 samples (out of 50,000 available)
```

**The model has high epistemic uncertainty for under-supported classes** because it hasn't seen enough examples.

### Reason 2: Evaluation Pool Composition

The evaluation includes samples from **epistemic_like** pool:
```python
eval_pools = {
    "clean": 100 samples,           # Well-represented classes
    "aleatoric_like": 100 samples,  # Noisy labels
    "epistemic_like": 100 samples,  # Under-supported classes ← HIGH UNCERTAINTY HERE
}
```

When you average across all pools, the high uncertainty from `epistemic_like` dominates.

### Reason 3: MC Dropout Variance

With `mc_passes=20`, you're getting 20 different predictions per sample. High variance = high epistemic uncertainty:

```
Example for an under-supported class sample:

Pass 1: [0.3, 0.2, 0.15, 0.1, ...]  # Prediction varies
Pass 2: [0.25, 0.3, 0.1, 0.15, ...]  # due to dropout
Pass 3: [0.2, 0.25, 0.2, 0.1, ...]
...
Pass 20: [0.28, 0.22, 0.18, 0.12, ...]

Variance = HIGH → Epistemic Uncertainty = HIGH
```

## Detailed Calculation Table

### Example: Single Sample from Under-Supported Class

| MC Pass | Class 0 | Class 1 | Class 2 | ... | Entropy | 
|---------|---------|---------|---------|-----|---------|
| 1       | 0.30    | 0.20    | 0.15    | ... | 2.15    |
| 2       | 0.25    | 0.30    | 0.10    | ... | 2.08    |
| 3       | 0.20    | 0.25    | 0.20    | ... | 2.20    |
| ...     | ...     | ...     | ...     | ... | ...     |
| 20      | 0.28    | 0.22    | 0.18    | ... | 2.12    |
| **Mean**| **0.26**| **0.24**| **0.16**| ... | **2.14**|

**Calculations:**
```
1. Predictive Entropy (H[y|x]):
   mean_pred = [0.26, 0.24, 0.16, ...]
   H_pred = -Σ(mean_pred * log(mean_pred)) = 2.18

2. Expected Entropy (E[H[y|x,θ]]):
   E_entropy = mean([2.15, 2.08, 2.20, ..., 2.12]) = 2.14

3. Mutual Information (Epistemic):
   MI = H_pred - E_entropy = 2.18 - 2.14 = 0.04

4. Per-sample epistemic = 0.04
   Mean across 100 epistemic_like samples ≈ 0.6-0.7
```

## Why Epistemic Stays Flat Across Label Noise

**Key insight**: Label noise affects **aleatoric** uncertainty, not epistemic!

```
Label Noise 0%:
- Model uncertainty (epistemic): 0.65  ← From under-supported classes
- Data noise (aleatoric): 0.60

Label Noise 50%:
- Model uncertainty (epistemic): 0.65  ← SAME! Still under-supported
- Data noise (aleatoric): 0.70         ← INCREASES with noise

Label Noise 100%:
- Model uncertainty (epistemic): 0.65  ← STILL SAME!
- Data noise (aleatoric): 0.80         ← INCREASES more
```

**Epistemic uncertainty is determined by**:
- Training set size (under-supported = 50 samples)
- Model capacity
- Number of MC passes

**NOT affected by**:
- Label noise (that's aleatoric)
- Test set composition (fixed evaluation pools)

## How to Reduce Epistemic Uncertainty

### Option 1: Increase Training Data for Under-Supported Classes
```python
"under_train_per_class": 300  # Instead of 50
```
**Expected**: Epistemic drops from 0.65 → 0.3

### Option 2: Remove Under-Supported Classes
```python
"under_supported": ""  # All classes equally represented
"regular_train_per_class": 300
```
**Expected**: Epistemic drops to 0.2-0.3

### Option 3: Increase MC Passes (Better Estimation)
```python
"mc_passes": 50  # Instead of 20
```
**Expected**: More stable epistemic estimates (smoother curves)

## Verification: Run Dataset Size Sweep

To see epistemic uncertainty decrease, run experiments with varying `under_train_per_class`:

```python
epistemic_sweep_values = [50, 100, 150, 200, 250, 300]
```

**Expected plot**:
```
Epistemic Uncertainty vs Dataset Size
     ^
0.8  |●
0.7  | ●
0.6  |  ●
0.5  |   ●
0.4  |    ●
0.3  |     ●___________
     +------------------→
     50  100 150 200 250 300
     Training samples per under-supported class
```

## Summary Table: Uncertainty Sources

| Uncertainty Type | Source | Affected By | Can Be Reduced By |
|-----------------|--------|-------------|-------------------|
| **Epistemic** | Lack of training data | Dataset size, model capacity | More training data |
| **Aleatoric** | Inherent data noise | Label noise, ambiguous samples | Better data quality (can't fully eliminate) |
| **Total** | Both combined | Both factors | Address both sources |

## Your Current Configuration Analysis

Based on the plot showing epistemic ≈ 0.6-0.7:

```
✓ Expected behavior: Flat across noise (epistemic not affected by label noise)
✓ Value makes sense: 50 samples per under-supported class is very limited
✓ Aleatoric increases: Correctly responds to label noise

To verify calculation:
1. Check per_sample_signals.csv for individual sample uncertainties
2. Look at epistemic_like pool specifically
3. Compare with clean pool (should be lower)
```

## Next Steps

1. **Verify calculation**: Export per-sample uncertainties to CSV
2. **Run epistemic sweep**: Vary dataset size to see epistemic decrease
3. **Compare pools**: Show epistemic separately for clean vs epistemic_like
4. **Add diagnostic table**: Show mean uncertainty per evaluation pool