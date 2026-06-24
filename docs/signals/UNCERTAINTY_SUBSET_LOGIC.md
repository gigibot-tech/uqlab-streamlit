# Uncertainty Subset Logic: Eval and DualXDA Training Data

> **Canonical eval summary:** [`docs/features/evaluation-protocol.md`](../features/evaluation-protocol.md) — end-to-end protocol (current vs proposed 4-region partition). This doc goes deeper on subset selection mechanics.

## Overview

This document explains how evaluation samples and DualXDA training subsets are selected for measuring different types of uncertainty (epistemic, aleatoric, hybrid).

## Key Concept: Different Uncertainties Need Different Data

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL CIFAR-10N DATASET                        │
│                    50,000 training samples                       │
│                    10,000 test samples                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │   EXPERIMENT CONFIGURATION SPLITS IT    │
        └─────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │  TRAINING SUBSET  │       │  EVALUATION POOL  │
    │  (for DualXDA)    │       │  (for testing)    │
    └───────────────────┘       └───────────────────┘
```

## 1. Training Subset Selection (for DualXDA)

### Purpose
DualXDA needs training data to compute attribution signals (mass, coherence, dominance). The training subset determines which samples can be "supporters" for test predictions.

### Configuration Parameters
```python
config = {
    "under_supported_classes": [0, 1],  # Classes with few samples
    "under_train_per_class": 50,        # Samples per under-supported class
    "regular_train_per_class": 300,     # Samples per regular class
    "noise_rate": 0.4,                  # Label noise rate
}
```

### Selection Logic
```python
def select_training_subset(full_train_data, config):
    """
    Select training samples for DualXDA based on experiment config.
    
    This creates EPISTEMIC uncertainty by limiting training data.
    """
    train_subset = []
    
    # 1. Under-supported classes (EPISTEMIC UNCERTAINTY SOURCE)
    for class_id in config["under_supported_classes"]:
        samples = full_train_data[class_id]
        # Take only N samples → creates epistemic uncertainty
        train_subset.extend(samples[:config["under_train_per_class"]])
    
    # 2. Regular classes
    regular_classes = [i for i in range(10) 
                      if i not in config["under_supported_classes"]]
    for class_id in regular_classes:
        samples = full_train_data[class_id]
        train_subset.extend(samples[:config["regular_train_per_class"]])
    
    # 3. Apply noise (ALEATORIC UNCERTAINTY SOURCE)
    # Keep samples matching target noise rate
    noisy_samples = [s for s in train_subset if s.is_noisy]
    clean_samples = [s for s in train_subset if not s.is_noisy]
    
    target_noisy_count = int(len(train_subset) * config["noise_rate"])
    final_subset = clean_samples + noisy_samples[:target_noisy_count]
    
    return final_subset
```

### Example
```
Configuration:
- Under-supported: classes [0, 1] with 50 samples each
- Regular: classes [2-9] with 300 samples each
- Noise rate: 40%

Training Subset:
┌─────────────────────────────────────────────────────────────┐
│ Class 0: 50 samples  (UNDER-SUPPORTED → Epistemic)         │
│ Class 1: 50 samples  (UNDER-SUPPORTED → Epistemic)         │
│ Class 2: 300 samples (Regular)                              │
│ Class 3: 300 samples (Regular)                              │
│ ...                                                          │
│ Class 9: 300 samples (Regular)                              │
│                                                              │
│ Total: 100 + 2400 = 2500 samples                           │
│ Of which 40% have noisy labels (ALEATORIC)                 │
└─────────────────────────────────────────────────────────────┘
```

## 2. Evaluation Pool Selection

### Purpose
Evaluation samples are used to TEST the model and measure uncertainty. Different uncertainty types need different evaluation samples.

### Configuration Parameter
```python
config = {
    "eval_per_group": 100,  # Samples per uncertainty group
}
```

### Three Evaluation Groups

#### Group 1: EPISTEMIC Uncertainty Samples
```python
def select_epistemic_eval_samples(remaining_data, config):
    """
    Select samples from UNDER-SUPPORTED classes.
    
    These samples should have HIGH epistemic uncertainty because
    the model was trained on very few examples from these classes.
    """
    epistemic_samples = []
    
    for class_id in config["under_supported_classes"]:
        # Get samples NOT used in training
        remaining = remaining_data[class_id]
        # Take eval_per_group samples
        epistemic_samples.extend(remaining[:config["eval_per_group"]])
    
    return epistemic_samples
```

**Example:**
```
Under-supported classes: [0, 1]
Training used: 50 samples per class
Remaining: ~4950 samples per class

Epistemic Eval Pool:
- Class 0: 100 samples (from remaining 4950)
- Class 1: 100 samples (from remaining 4950)
Total: 200 samples

Expected: HIGH epistemic uncertainty (model saw few training examples)
```

#### Group 2: ALEATORIC Uncertainty Samples
```python
def select_aleatoric_eval_samples(remaining_data, config):
    """
    Select samples with NOISY labels from REGULAR classes.
    
    These samples should have HIGH aleatoric uncertainty because
    their labels are inherently ambiguous/noisy.
    """
    aleatoric_samples = []
    
    regular_classes = [i for i in range(10) 
                      if i not in config["under_supported_classes"]]
    
    for class_id in regular_classes:
        remaining = remaining_data[class_id]
        # Filter for NOISY samples only
        noisy_samples = [s for s in remaining if s.is_noisy]
        aleatoric_samples.extend(noisy_samples[:config["eval_per_group"]])
    
    return aleatoric_samples
```

**Example:**
```
Regular classes: [2, 3, 4, 5, 6, 7, 8, 9]
Training used: 300 samples per class
Remaining: ~4700 samples per class

Aleatoric Eval Pool:
- Class 2: 100 NOISY samples
- Class 3: 100 NOISY samples
- ...
- Class 9: 100 NOISY samples
Total: 800 samples (all with noisy labels)

Expected: HIGH aleatoric uncertainty (inherent label ambiguity)
```

#### Group 3: CLEAN (Low Uncertainty) Samples
```python
def select_clean_eval_samples(remaining_data, config):
    """
    Select CLEAN samples from REGULAR classes.
    
    These samples should have LOW uncertainty because:
    - Model was trained on many examples (not under-supported)
    - Labels are clean (not noisy)
    """
    clean_samples = []
    
    regular_classes = [i for i in range(10) 
                      if i not in config["under_supported_classes"]]
    
    for class_id in regular_classes:
        remaining = remaining_data[class_id]
        # Filter for CLEAN samples only
        clean_samples_class = [s for s in remaining if not s.is_noisy]
        clean_samples.extend(clean_samples_class[:config["eval_per_group"]])
    
    return clean_samples
```

**Example:**
```
Regular classes: [2, 3, 4, 5, 6, 7, 8, 9]
Training used: 300 samples per class
Remaining: ~4700 samples per class

Clean Eval Pool:
- Class 2: 100 CLEAN samples
- Class 3: 100 CLEAN samples
- ...
- Class 9: 100 CLEAN samples
Total: 800 samples (all with clean labels)

Expected: LOW uncertainty (well-supported, clean labels)
```

## 3. How DualXDA Uses Training Subset

### Attribution Computation Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    EVALUATION SAMPLE                         │
│                    (e.g., airplane image)                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Model Forward  │
                    │  Get Prediction │
                    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   DualXDA       │
                    │   Attribution   │
                    └─────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────┐
        │  Search TRAINING SUBSET for supporters  │
        │  (samples that influenced this pred)    │
        └─────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
    ┌───────────────────┐       ┌───────────────────┐
    │  Top-K Supporters │       │  Compute Signals  │
    │  (e.g., 10 imgs)  │       │  - Mass           │
    │                   │       │  - Coherence      │
    │  Sample 1: +0.5   │       │  - Dominance      │
    │  Sample 2: +0.3   │       │  - Disagreement   │
    │  Sample 3: +0.1   │       │  ...              │
    │  ...              │       │                   │
    └───────────────────┘       └───────────────────┘
```

### Key Insight: Training Subset Size Affects Attribution

**Small Training Subset (Under-supported class):**
```
Training: 50 samples for class 0
Evaluation: Test sample from class 0

DualXDA Attribution:
- Searches among 50 training samples
- Finds top-10 supporters
- Mass: LOW (few samples to support)
- Coherence: LOW (supporters may disagree)
- Dominance: HIGH (few samples dominate)

Result: HIGH epistemic uncertainty detected!
```

**Large Training Subset (Regular class):**
```
Training: 300 samples for class 2
Evaluation: Test sample from class 2

DualXDA Attribution:
- Searches among 300 training samples
- Finds top-10 supporters
- Mass: HIGH (many samples support)
- Coherence: HIGH (supporters agree)
- Dominance: LOW (support distributed)

Result: LOW epistemic uncertainty detected!
```

## 4. Complete Example: One Experiment Configuration

### Configuration
```python
config = {
    "under_supported_classes": [0, 1],
    "under_train_per_class": 50,
    "regular_train_per_class": 300,
    "noise_rate": 0.4,
    "eval_per_group": 100,
}
```

### Data Split
```
FULL DATASET: 50,000 training + 10,000 test

TRAINING SUBSET (for DualXDA):
├─ Class 0: 50 samples (40% noisy)
├─ Class 1: 50 samples (40% noisy)
├─ Class 2: 300 samples (40% noisy)
├─ Class 3: 300 samples (40% noisy)
├─ ...
└─ Class 9: 300 samples (40% noisy)
Total: 2,500 samples

EVALUATION POOLS:
├─ Epistemic Group:
│  ├─ Class 0: 100 samples (from remaining 4,950)
│  └─ Class 1: 100 samples (from remaining 4,950)
│  Total: 200 samples
│
├─ Aleatoric Group:
│  ├─ Class 2: 100 NOISY samples
│  ├─ Class 3: 100 NOISY samples
│  ├─ ...
│  └─ Class 9: 100 NOISY samples
│  Total: 800 samples
│
└─ Clean Group:
   ├─ Class 2: 100 CLEAN samples
   ├─ Class 3: 100 CLEAN samples
   ├─ ...
   └─ Class 9: 100 CLEAN samples
   Total: 800 samples

REMAINING: ~45,700 samples (unused)
```

### Inference Flow

```
1. Train model on TRAINING SUBSET (2,500 samples)
   ↓
2. Deploy to watsonx.ai with training subset
   ↓
3. For each evaluation sample:
   ├─ Model predicts class
   ├─ DualXDA searches TRAINING SUBSET for supporters
   ├─ Computes attribution signals (mass, coherence, etc.)
   └─ Returns prediction + uncertainty signals
   ↓
4. Measure AUROC:
   ├─ Epistemic samples: Should have HIGH epistemic signals
   ├─ Aleatoric samples: Should have HIGH aleatoric signals
   └─ Clean samples: Should have LOW all signals
```

## 5. Why This Matters for watsonx.ai

### Single Deployment Strategy

**Option 1: Multiple Deployments (BAD)**
```
Deployment 1: Config A (10% noise, 2 under-supported)
Deployment 2: Config B (40% noise, 2 under-supported)
Deployment 3: Config C (10% noise, 3 under-supported)
...
Problem: Need 10+ deployments!
```

**Option 2: Parameterized Deployment (GOOD)**
```
Single Deployment:
- Contains FULL training data (all 50,000 samples)
- Receives config at inference time
- Dynamically selects training subset for DualXDA
- Dynamically selects eval samples

Benefits:
✅ One deployment for all experiments
✅ Can test new configs without redeployment
✅ Cost-effective
✅ Easy to manage
```

### Implementation
```python
# Client side (Streamlit)
client = ParameterizedScoringClient(...)

# Experiment 1
config1 = ExperimentConfig(
    noise_rate=0.1,
    under_supported_classes=[0, 1],
    under_train_per_class=50,
    regular_train_per_class=300,
    eval_per_group=100
)
results1 = client.score_with_config(eval_samples, config1)

# Experiment 2 (different config, SAME deployment!)
config2 = ExperimentConfig(
    noise_rate=0.4,
    under_supported_classes=[0, 1, 2],
    under_train_per_class=30,
    regular_train_per_class=250,
    eval_per_group=150
)
results2 = client.score_with_config(eval_samples, config2)
```

## Summary

1. **Training Subset**: Selected based on config, used by DualXDA for attribution
2. **Eval Pools**: Three groups (epistemic, aleatoric, clean) for measuring uncertainty
3. **DualXDA**: Searches training subset to find supporters and compute signals
4. **Parameterized Deployment**: Single watsonx.ai deployment handles all configs
5. **Dynamic Selection**: Server-side logic selects appropriate subsets at inference time

---

**Made with Bob** 🤖