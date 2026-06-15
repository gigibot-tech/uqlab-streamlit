# API Endpoints Explained

## 🔍 Understanding the Two Main Endpoints

### 1. `/api/v1/datasets/{dataset_name}/stats` - Dataset Statistics (READ-ONLY)

**Purpose**: Get information ABOUT the dataset WITHOUT loading it for training

**What it does**:
```python
# Streamlit calls this BEFORE creating experiment
stats = fetch_dataset_stats("cifar10", "worse_label")

# Returns:
{
    "total_samples": 50000,
    "num_classes": 10,
    "noise_rate": 0.094,  # 9.4% noisy labels
    "class_distribution": {...},
    "noisy_samples": 4700,
    "clean_samples": 45300
}
```

**Why it exists**:
- ✅ Shows user what they're working with
- ✅ Helps user make informed decisions
- ✅ Displays in UI BEFORE experiment starts
- ✅ Fast - just reads metadata, doesn't load images
- ✅ No training triggered

**When it's called**:
- Step 1 of progressive app (Dataset Selection)
- User selects dataset → immediately shows stats
- Happens BEFORE experiment creation

---

### 2. `/api/v1/experiments/no-auth` - Create & Run Experiment (WRITE + EXECUTE)

**Purpose**: Create experiment AND trigger the full ML pipeline

**What it does**:
```python
# Streamlit calls this AFTER user configures everything
response = requests.post(
    "/api/v1/experiments/no-auth",
    json={
        "name": "exp_20260604_123456",
        "config": {
            "dataset": {...},
            "model": {...},
            "training": {...},
            "evaluation": {...}
        }
    }
)

# Returns:
{
    "id": "abc123",
    "name": "exp_20260604_123456",
    "status": "pending",  # Will become "running" → "completed"
    "created_at": "2026-06-04T10:30:00Z"
}
```

**Why it exists**:
- ✅ Saves experiment config to database
- ✅ Triggers the FULL ML pipeline:
  1. Data loading (with actual images)
  2. Model training
  3. Uncertainty estimation
  4. Signal calculation
  5. Evaluation
- ✅ Runs asynchronously (doesn't block UI)
- ✅ User can check status later

**When it's called**:
- Step 5 of progressive app (Review & Launch)
- User clicks "🚀 Launch Experiment"
- Happens AFTER all configuration is complete

---

## 🔄 The Complete Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Selects Dataset                                │
│                                                              │
│ Streamlit → GET /datasets/cifar10/stats?noise_type=worse   │
│                                                              │
│ Backend:                                                     │
│   1. Load CIFAR10NDataset (metadata only)                  │
│   2. Count samples, calculate noise rate                    │
│   3. Return stats JSON                                      │
│                                                              │
│ Streamlit: Display stats to user                           │
│                                                              │
│ ⚠️ NO TRAINING YET - Just showing info                      │
└─────────────────────────────────────────────────────────────┘
                         │
                         │ User configures model, training, etc.
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: User Launches Experiment                            │
│                                                              │
│ Streamlit → POST /experiments/no-auth                       │
│             {config: {...}}                                  │
│                                                              │
│ Backend:                                                     │
│   1. Save experiment to database                            │
│   2. Trigger ML pipeline (async):                           │
│      a. Load FULL dataset (all images)                      │
│      b. Train model                                         │
│      c. Run evaluation                                      │
│      d. Calculate signals                                   │
│      e. Save results                                        │
│                                                              │
│ Streamlit: Show "Experiment created" message                │
│                                                              │
│ ✅ FULL TRAINING PIPELINE RUNNING                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤔 Why Two Separate Endpoints?

### Option 1: Combined (BAD ❌)
```python
# If we only had /experiments/no-auth:
response = create_experiment(config)
# Problem: User doesn't see dataset info until AFTER experiment starts
# Problem: Can't make informed decisions
# Problem: Slow - loads full dataset just to show stats
```

### Option 2: Separated (GOOD ✅)
```python
# First: Get stats (fast, read-only)
stats = get_dataset_stats("cifar10", "worse_label")
# User sees: "50,000 samples, 9.4% noise"
# User decides: "OK, I'll use 300 samples per class"

# Then: Create experiment (slow, full pipeline)
experiment = create_experiment(config)
# Now training starts with informed configuration
```

---

## 📊 Data Loading Comparison

### `/stats` Endpoint (Lightweight)
```python
def get_dataset_stats(dataset_name, noise_type):
    # Load metadata only
    dataset = CIFAR10NDataset(root="./data", noise_type=noise_type)
    
    # Quick operations (no image loading)
    total = len(dataset)  # Just count
    noise_rate = dataset.get_noise_rate()  # Read from file
    
    return {
        "total_samples": total,
        "noise_rate": noise_rate
    }
    # ⚡ Fast: ~100ms
```

### `/experiments/no-auth` → Training Pipeline (Heavy)
```python
def train_experiment(config):
    # Load FULL dataset with images
    dataset = CIFAR10NDataset(root="./data", noise_type=config["noise_type"])
    
    # Load ALL images into memory
    train_loader = DataLoader(dataset, batch_size=256)
    
    # Train model (SLOW)
    for epoch in range(12):
        for batch in train_loader:
            # Process 50,000 images
            # Forward pass, backward pass
            # Update weights
    
    # Evaluate, calculate signals, etc.
    # 🐌 Slow: ~20-30 minutes
```

---

## 🏗️ MLOps Perspective

### Phase 1: Exploration (Stats Endpoint)
```
User → "What data do I have?"
API → "50K samples, 10 classes, 9.4% noise"
User → "OK, I'll configure my experiment"
```

### Phase 2: Experimentation (Experiments Endpoint)
```
User → "Launch experiment with this config"
API → "Experiment created, ID: abc123"
Pipeline → Train → Evaluate → Store Results
User → "Check results later"
```

### Phase 3: Monitoring
```
User → "How's my experiment?"
API → GET /experiments/abc123
API → "Status: completed, Accuracy: 85%"
```

---

## 🎯 Summary

| Endpoint | Purpose | Speed | Triggers Training | When Used |
|----------|---------|-------|-------------------|-----------|
| `/datasets/{name}/stats` | Show dataset info | Fast (100ms) | ❌ No | Before experiment |
| `/experiments/no-auth` | Create & run experiment | Slow (20min) | ✅ Yes | After configuration |

**Key Insight**: 
- `/stats` = "Tell me about the data" (read-only, fast)
- `/experiments` = "Run the full ML pipeline" (write + execute, slow)

They serve different purposes in the MLOps workflow!