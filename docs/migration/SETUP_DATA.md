# Data Setup Guide

## One-Time Setup: Download CIFAR-10N Noisy Labels

The uncertainty classification experiments require CIFAR-10N noisy labels. This is a **one-time download** (~2.3 MB).

### Automatic Download

Run the download script:

```bash
cd uqlab-streamlit
python3 scripts/download_cifar10n.py
```

### What Gets Downloaded

- **File**: `CIFAR-10_human.pt` (2.3 MB)
- **Location**: `data/cifar10n/cifar-10-batches-py/CIFAR-10_human.pt`
- **Source**: [CIFAR-10-100N GitHub Repository](https://github.com/UCSC-REAL/cifar-10-100n)

### What Happens During First Experiment Run

When you run your first experiment, the system will:

1. **Download CIFAR-10 base dataset** (~170 MB) - shown as "Downloading..." in logs
   - This is a PyTorch/torchvision automatic download
   - Happens once, cached for future runs
   - Takes ~5 minutes depending on connection

2. **Load CIFAR-10N noisy labels** (already downloaded above)
   - Instant if you ran the download script
   - Otherwise shows warning and uses clean labels only

### Progress Tracking

The CIFAR-10 download shows progress in backend logs:
```
9%|███▋                                    | 15.7M/170M [00:24<04:54, 526kB/s]
```

**Note**: This progress is currently only visible in backend logs. Future enhancement will show it in the Streamlit UI as "Step 1: Downloading dataset (X%)" before training starts.

### Verify Setup

Check if files exist:

```bash
# CIFAR-10N noisy labels (you downloaded)
ls -lh uqlab-streamlit/data/cifar10n/cifar-10-batches-py/CIFAR-10_human.pt

# CIFAR-10 base dataset (auto-downloaded on first run)
ls -lh uqlab-streamlit/data/cifar10n/cifar-10-batches-py/data_batch_*
```

### Troubleshooting

**Error: "CIFAR-10N noisy labels are not available"**
- Run: `python3 scripts/download_cifar10n.py`

**Slow first experiment**
- Normal! CIFAR-10 base dataset (170 MB) downloads on first run
- Subsequent experiments will be much faster (data is cached)

### Future Enhancement

We plan to add a setup progress indicator in Streamlit:
- Step 1: Downloading CIFAR-10 dataset (X/100%)
- Step 2: Loading noisy labels
- Step 3: Extracting features
- Step 4: Training model (epoch X/Y)

This will make the one-time setup more transparent to users.