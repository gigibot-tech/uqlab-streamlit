# NumPy 2.x + torchvision Compatibility Fix

## Problem

When running experiments with NumPy 2.4.2 and torchvision 0.25.0, you get:

```
VisibleDeprecationWarning: dtype(): align should be passed as Python or NumPy boolean but got <class 'bool'>
```

This is a known compatibility issue between NumPy 2.x and torchvision's CIFAR dataset loader.

## Solution Options

### Option 1: Suppress the Warning (Quick Fix)

Add this at the top of your notebook or script:

```python
import warnings
warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
```

Or more specifically:

```python
import warnings
warnings.filterwarnings('ignore', message='.*dtype.*align.*')
```

### Option 2: Downgrade NumPy (Recommended for Stability)

```bash
pip install "numpy<2.0"
```

This will install NumPy 1.26.x which is fully compatible with torchvision 0.25.0.

### Option 3: Upgrade torchvision (If Available)

Check if a newer torchvision version is available that fixes this:

```bash
pip install --upgrade torchvision
```

## Implementation

For your experiments, add this to the top of your notebook:

```python
import warnings
import numpy as np

# Suppress NumPy 2.x deprecation warnings from torchvision
warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning)
warnings.filterwarnings('ignore', message='.*dtype.*align.*')
```

## Why This Happens

NumPy 2.0+ changed how the `align` parameter in `dtype()` should be passed. Torchvision's CIFAR dataset code uses the old style, triggering this warning. The warning itself is harmless, but it may be treated as an error in some contexts.

## Verification

After applying the fix, your experiments should run without this warning appearing.