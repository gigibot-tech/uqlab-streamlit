# Per-Class Sweep Visualization Explained

## Your Question

> "bro but we have f.e. under_train for specific classes only right, so how is it visualized?"

When you sweep only **class 4's training samples** (e.g., 10→300) while **class 5 stays constant** at 30 samples, how does the three-line plot show this?

## Answer: Pool-Based Aggregation

**Key Insight**: Evaluation pools are assigned based on **class membership**, NOT sweep status.

### How It Works

#### 1. Pool Assignment (Lines 136-142 in `fast_pilot_loader.py`)

```python
# Classes are assigned to pools based on their configuration
under_mask = np.isin(clean_labels, under_supported_classes)  # Classes 4-5
non_under_mask = ~under_mask                                  # Classes 0-3, 6-9

# Three evaluation pools:
clean_eval_pool = np.where(non_under_mask & clean_mask & ~train_mask)[0]
aleatoric_eval_pool = np.where(non_under_mask & noise_mask & ~train_mask)[0]
epistemic_eval_pool = np.where(under_mask & clean_mask & ~train_mask)[0]
```

**Critical Point**: If classes 4-5 are both configured as "sparse" (low `train_samples`), then:
- **ALL test samples from class 4** → epistemic pool
- **ALL test samples from class 5** → epistemic pool

The pool assignment is **class-based**, not **sweep-based**.

#### 2. Sweep Plot Aggregation (Lines 94-130 in `sweep_line_plot.py`)

```python
def build_sweep_line_plot(experiments, sweep_kind):
    for exp in experiments:
        # Load eval_group_labels: [0, 0, 2, 2, 1, 2, 0, ...]
        #   0 = clean, 1 = aleatoric, 2 = epistemic
        
        # Filter to epistemic pool only
        epistemic_mask = (eval_group_labels == GROUP_EPISTEMIC)
        
        # Compute mean uncertainty across ALL epistemic samples
        epistemic_uncertainty = signal_values[epistemic_mask].mean()
```

**What This Means**:
- The plot shows **mean uncertainty across the entire epistemic pool**
- This includes samples from **both class 4 (swept) AND class 5 (constant)**

### Concrete Example

#### Configuration
```yaml
per_class_config:
  4:  # Swept class
    train_samples: [10, 25, 50, 100, 200, 300]  # ← Varies
    sweep_epistemic: true
  5:  # Constant class
    train_samples: 30  # ← Fixed
    sweep_epistemic: false
```

#### What Happens in Each Experiment

| Experiment | Class 4 Train | Class 5 Train | Epistemic Pool Composition |
|------------|---------------|---------------|----------------------------|
| exp_1      | 10 samples    | 30 samples    | 100 test samples from class 4 + 100 from class 5 |
| exp_2      | 25 samples    | 30 samples    | 100 test samples from class 4 + 100 from class 5 |
| exp_3      | 50 samples    | 30 samples    | 100 test samples from class 4 + 100 from class 5 |
| exp_4      | 100 samples   | 30 samples    | 100 test samples from class 4 + 100 from class 5 |
| exp_5      | 200 samples   | 30 samples    | 100 test samples from class 4 + 100 from class 5 |
| exp_6      | 300 samples   | 30 samples    | 100 test samples from class 4 + 100 from class 5 |

#### Three-Line Plot Shows

```
Epistemic Uncertainty (solid red line):
  exp_1: mean([class_4_uncertainty, class_5_uncertainty]) = high (both sparse)
  exp_2: mean([class_4_uncertainty, class_5_uncertainty]) = medium-high
  exp_3: mean([class_4_uncertainty, class_5_uncertainty]) = medium
  exp_4: mean([class_4_uncertainty, class_5_uncertainty]) = medium-low
  exp_5: mean([class_4_uncertainty, class_5_uncertainty]) = low
  exp_6: mean([class_4_uncertainty, class_5_uncertainty]) = low
```

**Why the trend?**
- **Class 4**: Uncertainty decreases as training samples increase (10→300)
- **Class 5**: Uncertainty stays constant (always 30 samples)
- **Pool mean**: Decreases because class 4's improving uncertainty pulls down the average

### Visual Representation

```
Epistemic Pool = [Class 4 samples] + [Class 5 samples]
                      ↓                    ↓
                  (swept)              (constant)

Experiment 1:  [high uncertainty] + [high uncertainty] → mean = HIGH
Experiment 2:  [med uncertainty]  + [high uncertainty] → mean = MED-HIGH
Experiment 3:  [low uncertainty]  + [high uncertainty] → mean = MEDIUM
Experiment 6:  [very low uncert.] + [high uncertainty] → mean = LOW
```

## Why This Design?

### 1. **Semantic Consistency**
Pools represent **uncertainty types**, not sweep parameters:
- Epistemic pool = "samples from under-supported classes"
- Aleatoric pool = "samples with label noise"
- Clean pool = "samples from well-supported, clean classes"

### 2. **Realistic Evaluation**
In real-world scenarios:
- You don't know which specific classes will be under-supported
- You want to measure **overall epistemic uncertainty** across all sparse classes
- The pool aggregation simulates this realistic uncertainty

### 3. **Comparative Analysis**
By keeping class 5 constant:
- You can see how **increasing class 4's support** affects **overall epistemic uncertainty**
- The constant class 5 provides a **baseline** that shows the sweep's relative impact

## Code Flow

### 1. Data Loading (`fast_pilot_loader.py:47-200`)
```python
def sample_indices_for_fast_pilot(
    under_supported_classes=[4, 5],  # Both classes marked as sparse
    under_train_per_class=varies,    # Class 4: swept, Class 5: constant
):
    # Assign ALL samples from classes 4-5 to epistemic pool
    epistemic_eval_pool = np.where(under_mask & clean_mask & ~train_mask)[0]
```

### 2. Evaluation Setup (`fast_pilot_core.py:94-128`)
```python
def prepare_eval_data(epistemic_eval_pack):
    # Create group labels: 2 = epistemic
    eval_group_labels = torch.full((len(epistemic_eval_pack),), GROUP_EPISTEMIC)
    # All class 4 and class 5 test samples get label "2"
```

### 3. Plot Generation (`sweep_line_plot.py:94-130`)
```python
def build_sweep_line_plot(experiments):
    for exp in experiments:
        # Filter to epistemic pool (includes both class 4 and 5)
        epistemic_mask = (eval_group_labels == GROUP_EPISTEMIC)
        
        # Compute mean across ALL epistemic samples
        epistemic_uncertainty = signal_values[epistemic_mask].mean()
```

## Alternative: Per-Class Plots

If you want to see **individual class uncertainty**, you would need:

```python
# Hypothetical per-class visualization
for class_id in [4, 5]:
    class_mask = (eval_clean_labels == class_id)
    class_uncertainty = signal_values[class_mask].mean()
    plt.plot(sweep_values, class_uncertainty, label=f"Class {class_id}")
```

This is **not currently implemented** because:
1. The research protocol focuses on **pool-level** uncertainty
2. Per-class plots would require 10 lines (one per class) → cluttered
3. Pool aggregation is the **standard evaluation metric** in UQ research

## Summary

**Your Question**: How is class 4 (swept) vs class 5 (constant) visualized?

**Answer**: 
- Both classes' test samples go into the **epistemic pool**
- The plot shows **mean uncertainty across the entire pool**
- As class 4's training increases, its uncertainty decreases
- Class 5's uncertainty stays constant
- The **pool mean** decreases because class 4 pulls it down

**Key Takeaway**: Pool assignment is **class-based** (determined by `under_supported_classes`), not **sweep-based** (determined by which parameter varies). The three-line plot shows **aggregate pool-level uncertainty**, not per-class uncertainty.

## Related Files

- **Pool Assignment**: [`fast_pilot_loader.py:136-142`](src/uqlab/data/fast_pilot_loader.py)
- **Evaluation Setup**: [`fast_pilot_core.py:94-128`](src/uqlab/runner/fast_pilot_core.py)
- **Plot Generation**: [`sweep_line_plot.py:94-130`](src/uqlab/evaluation/classification/pipeline/sweep_line_plot.py)
- **Pool Expectations**: [`sweep_plot_pools.py:1-150`](src/uqlab/evaluation/classification/pipeline/sweep_plot_pools.py)

## See Also

- [`THREE_LINE_PLOT_EXPLAINED.md`](src/uqlab/evaluation/classification/pipeline/THREE_LINE_PLOT_EXPLAINED.md) - General plot mechanics
- [`POOL_FILTERED_SWEEP_PLOT_DATA_FLOW.md`](POOL_FILTERED_SWEEP_PLOT_DATA_FLOW.md) - Complete data flow
- [`PER_CLASS_CONFIG_IMPLEMENTATION_PLAN.md`](PER_CLASS_CONFIG_IMPLEMENTATION_PLAN.md) - Per-class configuration design