# Simple Architecture Overview

You're right - an experiment should be just a few lines! Here's the **essential flow**:

## The Core Idea (10 Lines of Code)

```python
# 1. Load data
dataset = CIFAR10NDataset(noise_type="worse_label")
split = sample_indices_for_fast_pilot(dataset, under_supported_classes=[3,5])

# 2. Extract features
features = extract_features(dataset, split.train_indices, model="dinov2")

# 3. Train classifier
model = train_feature_model(features, epochs=12, dropout=0.2)

# 4. Compute uncertainty
uncertainty_scores = compute_mc_dropout_uncertainty(model, eval_features, mc_passes=20)

# 5. Evaluate
auroc = binary_auroc(uncertainty_scores, is_noisy_mask)
```

That's it! Everything else is **infrastructure**.

## Your Module Structure (Simplified)

### Core Pipeline (3 modules)
```
1. data_loader.py        → Load & sample data
2. models.py             → Train classifier  
3. evaluation.py         → Compute metrics
```

### Supporting Modules (3 modules)
```
4. attribution_signals.py → DualXDA uncertainty signals
5. utils.py              → Helper functions (seed, device, transforms)
6. unified_tracker.py    → Save results
```

### Optional/UI (3 modules)
```
7. config_schema.py      → Config validation (NEW)
8. watsonx_streamlit.py  → Cloud inference UI
9. streamlit_viz_app.py  → Visualization dashboard
```

## What Each Module Does (One Sentence)

| Module | Purpose | Lines |
|--------|---------|-------|
| `data_loader.py` | Sample train/eval splits with controlled uncertainty | 549 |
| `models.py` | Simple MLP with dropout | 100 |
| `evaluation.py` | AUROC, F1, confusion matrix | 300 |
| `attribution_signals.py` | DualXDA-based uncertainty signals | 200 |
| `utils.py` | Seed, device, transforms | 50 |
| `unified_tracker.py` | Save experiment results | 200 |

**Total core: ~1,400 lines** (reasonable for research code)

## The Actual Experiment Script

Your main script (`scripts/run_fast_uncertainty_classification.py`) is ~400 lines, but the **actual experiment logic** is ~50 lines:

```python
# Simplified version of your experiment
def run_experiment(config):
    # 1. Setup (5 lines)
    set_seed(config.seed)
    device = auto_device(config.device)
    dataset = CIFAR10NDataset(noise_type=config.noise_type)
    
    # 2. Sample data (3 lines)
    split = sample_indices_for_fast_pilot(
        dataset, 
        under_supported_classes=parse_classes(config.under_supported),
        under_train_per_class=config.under_train_per_class,
        regular_train_per_class=config.regular_train_per_class,
        eval_per_group=config.eval_per_group,
    )
    
    # 3. Extract features (10 lines)
    organizer = EmbeddingOrganizer(dataset, split, ...)
    organizer.load_or_compute_features()
    train_pack = organizer.get_train_pack()
    eval_packs = {
        'clean': organizer.get_clean_eval_pack(),
        'aleatoric': organizer.get_aleatoric_eval_pack(),
        'epistemic': organizer.get_epistemic_eval_pack(),
    }
    
    # 4. Train model (5 lines)
    train_dataset = EmbeddingDataset(train_pack)
    model = train_feature_model(
        train_dataset,
        epochs=config.epochs,
        learning_rate=config.learning_rate,
        dropout=config.dropout,
    )
    
    # 5. Compute uncertainty (10 lines)
    for name, pack in eval_packs.items():
        # MC Dropout uncertainty
        uncertainty = calculate_mc_dropout_uncertainty(
            model, pack['features'], mc_passes=config.mc_passes
        )
        
        # DualXDA attribution signals
        signals = compute_attribution_structure_signals(
            tracer, model, pack['features'], train_dataset
        )
    
    # 6. Evaluate (5 lines)
    results = {}
    for signal_name, signal_values in signals.items():
        auroc = binary_auroc(signal_values, pack['is_noisy'])
        results[f"{name}_{signal_name}_auroc"] = auroc
    
    # 7. Save (2 lines)
    tracker.log_metrics(results)
    tracker.save_results()
    
    return results
```

**That's ~40 lines of actual logic!** The rest is:
- Error handling
- Progress bars
- Logging
- Config parsing
- Result formatting

## Why It Feels Complex

Your code has **good abstractions** but they hide the simplicity:

### Without Abstractions (Clear but Repetitive)
```python
# Load data
dataset = CIFAR10NDataset(...)
train_indices = sample_train_indices(...)
eval_indices = sample_eval_indices(...)

# Extract features
train_features = []
for idx in train_indices:
    img, label = dataset[idx]
    feat = dinov2_model(img)
    train_features.append(feat)

# Train
model = MLP(...)
for epoch in range(epochs):
    for batch in train_loader:
        loss = criterion(model(batch), labels)
        loss.backward()
        optimizer.step()

# Evaluate
predictions = []
for sample in eval_features:
    pred = model(sample)
    predictions.append(pred)
auroc = compute_auroc(predictions, labels)
```

### With Your Abstractions (Concise but Hides Details)
```python
organizer = EmbeddingOrganizer(dataset, split, ...)
organizer.load_or_compute_features()
train_pack = organizer.get_train_pack()

model = train_feature_model(train_dataset, epochs=12)

uncertainty = calculate_mc_dropout_uncertainty(model, eval_features)
auroc = binary_auroc(uncertainty, is_noisy)
```

**Your abstractions are GOOD!** They just hide the complexity.

## How to Understand Your Code Better

### 1. Start with the High-Level Flow
Read `scripts/run_fast_uncertainty_classification.py` and identify the 6 steps:
1. Setup
2. Sample data
3. Extract features
4. Train model
5. Compute uncertainty
6. Evaluate

### 2. Understand Each Abstraction

**`EmbeddingOrganizer`** (data_loader.py:379)
```python
# What it does: Manages feature extraction and caching
# Why: Avoid re-computing DINOv2 features every run
# Core methods:
#   - load_or_compute_features() → Extract/load 768-dim embeddings
#   - get_train_pack() → Get training features
#   - get_clean_eval_pack() → Get clean eval features
```

**`train_feature_model`** (data_loader.py:317)
```python
# What it does: Train MLP on pre-extracted features
# Why: Fast training on embeddings vs full images
# Core logic: Standard PyTorch training loop
```

**`compute_attribution_structure_signals`** (attribution_signals.py:69)
```python
# What it does: Compute DualXDA uncertainty signals
# Why: Attribution-based uncertainty quantification
# Core signals:
#   - mass: Sum of attribution magnitudes
#   - coherence: Ratio of signed/unsigned sum
#   - label_disagreement: Entropy of supporter labels
```

### 3. Draw the Data Flow

```
CIFAR-10N Images (50k)
    ↓
sample_indices_for_fast_pilot()
    ↓
Train: 3,500 images | Eval: 1,800 images
    ↓
extract_features_for_indices() [DINOv2]
    ↓
768-dim embeddings (cached)
    ↓
train_feature_model() [MLP + Dropout]
    ↓
Trained classifier
    ↓
calculate_mc_dropout_uncertainty() [20 passes]
    ↓
Uncertainty scores
    ↓
binary_auroc()
    ↓
AUROC metric (0-1)
```

### 4. Simplify Your Mental Model

**Think of it as 3 stages:**

1. **Data Stage** (data_loader.py)
   - Input: Raw images
   - Output: 768-dim embeddings + labels

2. **Model Stage** (models.py + data_loader.py)
   - Input: Embeddings
   - Output: Trained classifier

3. **Evaluation Stage** (evaluation.py + attribution_signals.py)
   - Input: Classifier + eval embeddings
   - Output: AUROC scores

## Bottom Line

**Your code IS simple at its core!** The complexity comes from:
- ✅ **Good abstractions** (EmbeddingOrganizer, etc.)
- ✅ **Feature caching** (avoid re-computing)
- ✅ **Multiple uncertainty signals** (MC Dropout + DualXDA)
- ✅ **Proper experiment tracking** (save results, configs)

**To understand it better:**
1. Read the main script first (top-down)
2. Understand each abstraction (what/why)
3. Draw the data flow
4. Ignore infrastructure code (logging, progress bars, etc.)

**The actual ML logic is ~50 lines. Everything else is making it production-ready.**

## Made with Bob