# Signal Structure: 7 Signals × 2 Uncertainty Types

## What Does "7 × 2" Mean?

Each of the 7 individual attribution signals can detect BOTH types of uncertainty:
- **Aleatoric** (noisy/ambiguous labels)
- **Epistemic** (under-supported classes)

So we get 7 × 2 = **14 individual signal AUROC values** per experiment.

## Visual Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    INDIVIDUAL SIGNALS (7)                        │
└─────────────────────────────────────────────────────────────────┘

1. msp_uncertainty
   ├─ Aleatoric AUROC: How well it detects noisy labels
   └─ Epistemic AUROC: How well it detects under-supported classes

2. predictive_entropy
   ├─ Aleatoric AUROC: How well it detects noisy labels
   └─ Epistemic AUROC: How well it detects under-supported classes

3. mutual_info
   ├─ Aleatoric AUROC: How well it detects noisy labels
   └─ Epistemic AUROC: How well it detects under-supported classes

4. inverse_coherence (DualXDA attribution)
   ├─ Aleatoric AUROC: How well it detects noisy labels
   └─ Epistemic AUROC: How well it detects under-supported classes

5. dominance (DualXDA attribution)
   ├─ Aleatoric AUROC: How well it detects noisy labels
   └─ Epistemic AUROC: How well it detects under-supported classes

6. inverse_mass (Representer Theorem)
   ├─ Aleatoric AUROC: How well it detects noisy labels
   └─ Epistemic AUROC: How well it detects under-supported classes

7. inverse_logit_magnitude (Representer Theorem)
   ├─ Aleatoric AUROC: How well it detects noisy labels
   └─ Epistemic AUROC: How well it detects under-supported classes

┌─────────────────────────────────────────────────────────────────┐
│                    AGGREGATED (2) - OLD STYLE                    │
└─────────────────────────────────────────────────────────────────┘

8. epistemic_auroc (AGGREGATED)
   └─ Combines multiple signals to detect epistemic uncertainty
      (This is what you currently see)

9. aleatoric_auroc (AGGREGATED)
   └─ Combines multiple signals to detect aleatoric uncertainty
      (This is what you currently see)
```

## Example with Real Numbers

Let's say you sweep `under_train_per_class` from 50 to 100:

### Run 1: under_train_per_class = 50

```
Individual Signals:
├─ msp_uncertainty_aleatoric:     0.82
├─ msp_uncertainty_epistemic:     0.75
├─ predictive_entropy_aleatoric:  0.79
├─ predictive_entropy_epistemic:  0.73
├─ mutual_info_aleatoric:         0.81
├─ mutual_info_epistemic:         0.71
├─ inverse_coherence_aleatoric:   0.73  ← Best for aleatoric!
├─ inverse_coherence_epistemic:   0.68
├─ dominance_aleatoric:           0.65
├─ dominance_epistemic:           0.76
├─ inverse_mass_aleatoric:        0.71
├─ inverse_mass_epistemic:        0.94  ← Best for epistemic!
├─ inverse_logit_magnitude_alea:  0.69
└─ inverse_logit_magnitude_epis:  0.88

Aggregated (what you see now):
├─ epistemic_auroc:  0.85  ← Combination of above
└─ aleatoric_auroc:  0.73  ← Combination of above
```

### Run 2: under_train_per_class = 100

```
Individual Signals:
├─ msp_uncertainty_aleatoric:     0.84
├─ msp_uncertainty_epistemic:     0.72
├─ predictive_entropy_aleatoric:  0.81
├─ predictive_entropy_epistemic:  0.70
... (14 values total)

Aggregated:
├─ epistemic_auroc:  0.82
└─ aleatoric_auroc:  0.75
```

## What You'll See in the Visualization

### Current (Only Aggregated):
```
Chart shows 2 lines:
- Epistemic AUROC (Aggregated): 50→0.85, 100→0.82
- Aleatoric AUROC (Aggregated): 50→0.73, 100→0.75
```

### After Running New Experiments (All Signals):
```
Chart shows 16 lines:
- msp_uncertainty (Aleatoric): 50→0.82, 100→0.84
- msp_uncertainty (Epistemic): 50→0.75, 100→0.72
- predictive_entropy (Aleatoric): 50→0.79, 100→0.81
- predictive_entropy (Epistemic): 50→0.73, 100→0.70
- ... (14 individual signal lines)
- Epistemic AUROC (Aggregated): 50→0.85, 100→0.82
- Aleatoric AUROC (Aggregated): 50→0.73, 100→0.75
```

## Why This Matters

### Aggregated View (Current)
- ✅ Simple: Just 2 numbers
- ❌ Can't see which signal is best
- ❌ Can't see signal-specific trends
- ❌ Can't optimize individual signals

### Per-Signal View (New)
- ✅ See which signal performs best for each uncertainty type
- ✅ Identify signal-specific parameter sensitivities
- ✅ Understand trade-offs between signals
- ✅ Make informed decisions about which signals to use

## Example Insights from Per-Signal View

Looking at the individual signals, you might discover:

1. **inverse_mass** is the best epistemic detector (0.94 AUROC)
2. **inverse_coherence** is the best aleatoric detector (0.73 AUROC)
3. **msp_uncertainty** is most stable across parameter changes
4. **dominance** improves dramatically with more training data
5. Some signals are redundant (highly correlated)

You can't see any of this with just the aggregated values!

## How to Get This Data

The per-signal data is captured in `result_summary_json` when experiments run.

**Your current experiments** only have:
```json
{
  "epistemic_auroc": 0.85,
  "aleatoric_auroc": 0.73
}
```

**New experiments** will have:
```json
{
  "epistemic_auroc": 0.85,
  "aleatoric_auroc": 0.73,
  "one_vs_rest_auroc": [
    {"signal": "msp_uncertainty", "aleatoric_like_auroc": 0.82, "epistemic_like_auroc": 0.75},
    {"signal": "inverse_coherence", "aleatoric_like_auroc": 0.73, "epistemic_like_auroc": 0.68},
    ... (7 signals total)
  ]
}
```

That's why you need to run new experiments - the old ones don't have this detailed breakdown!