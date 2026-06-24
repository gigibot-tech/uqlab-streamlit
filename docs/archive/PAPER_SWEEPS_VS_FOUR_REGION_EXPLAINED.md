# Paper Sweeps vs Four-Region Mode: Complete Explanation

## TL;DR

**Paper Sweeps (Fig. 3 & Fig. 4)** = Two separate 1D campaigns that vary ONE parameter at a time
**Four-Region Mode** = ONE run with all uncertainty types active simultaneously

**They CANNOT be combined** because they represent fundamentally different experimental designs.

---

## Paper Sweeps (Current Implementation)

### What They Are

The paper sweeps reproduce the disentanglement benchmark from the research paper. They test how well uncertainty signals can distinguish between:
- **Epistemic uncertainty** (lack of training data)
- **Aleatoric uncertainty** (label noise)

### How They Work

**Two separate 1D campaigns:**

#### Fig. 3 — Epistemic Sweep
```yaml
# Run 1
under_train_per_class: 25
aleatoric_noise_percentage: 0  # FIXED

# Run 2
under_train_per_class: 50
aleatoric_noise_percentage: 0  # FIXED

# Run 3
under_train_per_class: 100
aleatoric_noise_percentage: 0  # FIXED

# ... etc (5 runs total)
```

**Goal**: Show that epistemic uncertainty signals (like `inverse_mass`) correlate with dataset size

#### Fig. 4 — Aleatoric Sweep
```yaml
# Run 1
under_train_per_class: 30  # FIXED
aleatoric_noise_percentage: 0

# Run 2
under_train_per_class: 30  # FIXED
aleatoric_noise_percentage: 25

# Run 3
under_train_per_class: 30  # FIXED
aleatoric_noise_percentage: 50

# ... etc (5 runs total)
```

**Goal**: Show that aleatoric uncertainty signals (like `inverse_coherence`) correlate with label noise

### Evaluation Pools (3 pools)

Each run creates **3 evaluation pools**:

| Pool | What it contains | When populated |
|------|------------------|----------------|
| **Clean** | Regular classes, clean labels | Always |
| **Aleatoric-like** | Regular classes, noisy labels | Only when `aleatoric_noise_percentage > 0` |
| **Epistemic-like** | Under-supported classes, clean labels | Only when `under_train < regular_train` |

**Key insight**: In Fig. 3 sweeps, the aleatoric pool is **empty** (0% noise). In Fig. 4 sweeps, the epistemic pool may be **small** (fixed under-train).

### Class Assignment (Global)

```yaml
# Example for CIFAR-10 (10 classes: 0-9)
under_supported_classes: [4, 5]  # These get sparse training
regular_classes: [0, 1, 2, 3, 6, 7, 8, 9]  # These get full training

# Noise is applied GLOBALLY to all regular classes
aleatoric_noise_percentage: 25  # 25% of regular class samples get wrong labels
```

---

## Four-Region Mode (Proposed)

### What It Is

A **different experimental design** where you explicitly partition all 10 CIFAR-10 classes into **4 distinct regions**, each with its own training policy.

### How It Works

**ONE run with 4 class blocks:**

```yaml
partition_mode: four_region
class_regions:
  noisy:
    classes: [0, 1, 2, 3]      # 4 classes
    train_fraction: 1.0         # Use all available training data
    label_flip_pct: 30          # But flip 30% of labels
    
  sparse:
    classes: [4, 5]             # 2 classes
    train_fraction: 0.10        # Use only 10% of training data
    label_flip_pct: 0           # Keep labels clean
    
  clean:
    classes: [6, 7]             # 2 classes
    train_fraction: 1.0         # Use all training data
    label_flip_pct: 0           # Keep labels clean
    
  ood:
    classes: [8, 9]             # 2 classes
    train_fraction: 0.0         # ZERO training samples
    # These classes never seen during training
```

### Evaluation Pools (4 pools)

Each run creates **4 evaluation pools**:

| Pool | What it contains | Region source |
|------|------------------|---------------|
| **Aleatoric-like** | Held-out samples from noisy region | Classes 0-3 |
| **Epistemic-like** | Held-out samples from sparse region | Classes 4-5 |
| **Clean** | Held-out samples from clean region | Classes 6-7 |
| **OOD** | Test samples from OOD region | Classes 8-9 |

**Key insight**: All 4 pools are **populated in every run**. You get simultaneous evaluation of all uncertainty types.

### Class Assignment (Per-Region)

```yaml
# Each class belongs to EXACTLY ONE region
# Union of all regions = all 10 classes
# Regions are disjoint (no overlap)

Classes 0-3: Noisy region   → Aleatoric uncertainty
Classes 4-5: Sparse region  → Epistemic uncertainty  
Classes 6-7: Clean region   → Baseline (low uncertainty)
Classes 8-9: OOD region     → Out-of-distribution
```

---

## Why They Cannot Be Combined

### Fundamental Incompatibility

| Aspect | Paper Sweeps | Four-Region |
|--------|--------------|-------------|
| **Experimental goal** | Vary ONE parameter to test correlation | Test ALL uncertainty types simultaneously |
| **Number of runs** | 5-10 runs per sweep | 1 run |
| **Class assignment** | Global (2 under-supported + 8 regular) | Per-region (4 blocks of 2-4 classes each) |
| **Noise application** | Global % across all regular classes | Per-region % (only noisy region) |
| **Training budget** | Global counts (`under_train_per_class`, `regular_train_per_class`) | Per-region fractions (10%, 100%, 0%) |
| **What varies** | Parameter sweep (dataset size OR noise) | Nothing (fixed configuration) |
| **Plot output** | Line plot: X = swept parameter, Y = uncertainty/accuracy | Dashboard: 4 pool means in one run |

### Conceptual Difference

**Paper Sweeps ask**: "How does uncertainty signal X change when I vary parameter Y?"
- Fig. 3: "Does epistemic uncertainty decrease as I add more training data?"
- Fig. 4: "Does aleatoric uncertainty increase as I add more label noise?"

**Four-Region asks**: "In a single model, how do different uncertainty signals behave across different data regimes?"
- "Can the model detect noisy labels in classes 0-3?"
- "Can the model detect sparse training in classes 4-5?"
- "Does the model show low uncertainty on clean classes 6-7?"
- "Can the model detect OOD samples from classes 8-9?"

### Technical Incompatibility

1. **Config structure conflict**:
   ```yaml
   # Paper sweeps use:
   under_supported_classes: [4, 5]
   under_train_per_class: 50  # Swept in Fig. 3
   aleatoric_noise_percentage: 25  # Swept in Fig. 4
   
   # Four-region uses:
   partition_mode: four_region
   class_regions:
     noisy: { classes: [0,1,2,3], ... }
     sparse: { classes: [4,5], ... }
     # ... etc
   ```

2. **Sweep semantics conflict**:
   - Paper sweeps: "Run this config 5 times with different values"
   - Four-region: "Run this config once with all regions active"

3. **Plot semantics conflict**:
   - Paper sweeps: Line plot with swept parameter on X-axis
   - Four-region: Fixed-run dashboard with 4 pool comparisons

---

## What "Mirror Mode" Actually Means

### In Paper Sweeps Context

When you run a **1D sweep** (varying only one parameter), the plot can show a "mirror" line for the complementary uncertainty type:

#### Fig. 3 (Epistemic Sweep) with Mirror
```
Primary line (solid):   epistemic uncertainty vs under_train_per_class
Mirror line (dashed):   aleatoric uncertainty vs under_train_per_class
Accuracy line (dotted): model accuracy vs under_train_per_class
```

Even though noise is fixed at 0%, you can still compute aleatoric uncertainty signals and see how they behave (they should stay flat or low).

#### Fig. 4 (Aleatoric Sweep) with Mirror
```
Primary line (solid):   aleatoric uncertainty vs label_noise_percent
Mirror line (dashed):   epistemic uncertainty vs label_noise_percent
Accuracy line (dotted): model accuracy vs label_noise_percent
```

Even though under-train is fixed, you can still compute epistemic uncertainty signals and see how they behave.

### NOT Related to Four-Region

"Mirror mode" does **NOT** mean "run four-region mode". It means "show the complementary uncertainty type as a dashed line in 1D sweep plots".

---

## Summary Table

| Feature | Paper Sweeps (Fig. 3 & 4) | Four-Region Mode |
|---------|---------------------------|------------------|
| **Purpose** | Test signal-parameter correlation | Test multi-regime model behavior |
| **Runs needed** | 5-10 per sweep | 1 |
| **Parameters varied** | 1 per sweep | 0 (fixed config) |
| **Class assignment** | Global (2 types) | Per-region (4 types) |
| **Eval pools** | 3 (clean, aleatoric, epistemic) | 4 (clean, aleatoric, epistemic, OOD) |
| **Noise policy** | Global % | Per-region % |
| **Training budget** | Global counts | Per-region fractions |
| **Plot type** | Line plot (swept parameter) | Dashboard (fixed run) |
| **Implementation status** | ✅ Implemented | ⚠️ Proposed (not yet implemented) |
| **Use case** | Reproduce paper results | Comprehensive single-run benchmark |

---

## What You Should Do

For your task:

1. **Launch Fig. 3 (Epistemic Sweep)**:
   - Sweep `under_train_per_class`: [25, 50, 100, 150, 200]
   - Fix `aleatoric_noise_percentage`: 0
   - Under-supported classes: [4, 5]

2. **Launch Fig. 4 (Aleatoric Sweep)**:
   - Sweep `label_noise_percent`: [0, 25, 50, 75, 100]
   - Fix `under_train_per_class`: 30
   - Under-supported classes: [4, 5]

These are **two separate campaigns** using the **paper sweep mode** (legacy partition mode).

**Do NOT try to combine them with four-region mode** — they are incompatible experimental designs.

---

## Why the Pre-Launch Info Might Be Confusing

The confusion likely comes from:

1. **Terminology overlap**: "Mirror" sounds like it might relate to "four regions" but it doesn't
2. **Multiple modes**: The codebase supports both paper sweeps and (proposed) four-region mode
3. **Documentation mixing**: Docs describe both current (paper sweeps) and future (four-region) approaches
4. **Eval pool naming**: "aleatoric-like" and "epistemic-like" pools exist in BOTH modes but mean different things

The key is: **Paper sweeps = 1D parameter variation**. **Four-region = fixed multi-regime partition**. They serve different research questions.