# Signal Names Centralization - Best Practice & Implementation

**Date**: 2026-06-18  
**Issue**: Hardcoded signal names in visualization code instead of using centralized constants

## 🎯 Software Engineering Best Practice: Single Source of Truth (SSOT)

### The Principle

**Don't Repeat Yourself (DRY)** and **Single Source of Truth (SSOT)** dictate that:

1. **Define once**: Constants, configurations, and data structures should be defined in ONE canonical location
2. **Import everywhere**: All other code should import from that single source
3. **Iterate from source**: When you need to loop over items, use the centralized list

### Why This Matters

**❌ Bad Practice** (Current state):
```python
# File 1: shared/types.py
SIGNAL_NAMES = ["msp_uncertainty", "predictive_entropy", "mutual_info", ...]

# File 2: ui_components/visualization/analysis/uq_benchmarks.py
signal_names = [  # ← HARDCODED DUPLICATE!
    'msp_uncertainty',
    'predictive_entropy',
    'mutual_info',
    'inverse_coherence',
    'dominance',
    'inverse_mass',
    'inverse_logit_magnitude'
]
```

**Problems**:
- 🐛 **Bugs**: If you add a signal to `SIGNAL_NAMES`, visualization breaks
- 🔄 **Maintenance**: Must update multiple files for one change
- ❌ **Inconsistency**: Different files may have different lists
- 🧪 **Testing**: Hard to ensure all locations stay in sync

**✅ Good Practice** (Target state):
```python
# File 1: shared/types.py (SINGLE SOURCE OF TRUTH)
SIGNAL_NAMES = ["msp_uncertainty", "predictive_entropy", "mutual_info", ...]

# File 2: ui_components/visualization/analysis/uq_benchmarks.py
from uqlab.shared.types import SIGNAL_NAMES  # ← IMPORT!

# Use it directly
for idx, signal_name in enumerate(SIGNAL_NAMES):
    plot_signal(signal_name)
```

**Benefits**:
- ✅ **Single update**: Change once, works everywhere
- ✅ **Consistency**: All code uses same list
- ✅ **Type safety**: IDE autocomplete works
- ✅ **Testable**: Easy to verify correctness

---

## 📊 Current State Analysis

### Canonical Sources (GOOD ✅)

We have **TWO** canonical sources:

#### 1. `shared/types.py::SIGNAL_NAMES` (7 signals)
```python
SIGNAL_NAMES = [
    "msp_uncertainty",
    "predictive_entropy",
    "mutual_info",
    "inverse_coherence",
    "dominance",
    "inverse_mass",
    "inverse_logit_magnitude",
]
```

#### 2. `run_artifacts.py::FAST_PILOT_SIGNAL_NAMES` (8 signals)
```python
FAST_PILOT_SIGNAL_NAMES = (
    "msp_uncertainty",
    "predictive_entropy",
    "mutual_info",
    "coherence",              # ← Extra signal!
    "inverse_coherence",
    "dominance",
    "inverse_mass",
    "inverse_logit_magnitude",
)
```

**Note**: `FAST_PILOT_SIGNAL_NAMES` includes `"coherence"` (not inverse), used for CSV output.

### Hardcoded Duplicates (BAD ❌)

Found **5 locations** with hardcoded signal lists:

1. **`ui_components/visualization/analysis/uq_benchmarks.py:267`** ← **TARGET FOR FIX**
   ```python
   signal_names = [
       'msp_uncertainty',
       'predictive_entropy',
       'mutual_info',
       'inverse_coherence',
       'dominance',
       'inverse_mass',
       'inverse_logit_magnitude'
   ]
   ```

2. **`evaluation/benchmarks/visualization.py:113`**
   ```python
   for signal_name in ['msp_uncertainty', 'predictive_entropy', 'mutual_info',
                       'inverse_coherence', 'dominance', 'inverse_mass',
                       'inverse_logit_magnitude']:
   ```

3. **`results_io.py:11`** (Duplicate of `SIGNAL_NAMES`)
   ```python
   SIGNAL_NAMES = [
       "msp_uncertainty",
       ...
   ]
   ```

4. **`shared/notebook_utils/signals.py:7`** (Another duplicate)
   ```python
   SIGNAL_NAMES = [
       "msp_uncertainty",
       ...
   ]
   ```

5. **Legacy scripts** (multiple files in `scripts/legacy/`)

---

## 🔧 Solution: Centralize and Import

### Step 1: Identify the Canonical Source

**Decision**: Use `shared/types.py::SIGNAL_NAMES` as the **single source of truth**

**Rationale**:
- ✅ Already imported in many places
- ✅ Part of shared types module
- ✅ Exported via `shared/__init__.py`
- ✅ Includes all production signals (7 signals)

### Step 2: Fix Hardcoded Locations

#### Priority 1: Active Code (Fix Now)

**File**: `ui_components/visualization/analysis/uq_benchmarks.py`

**Current** (lines 266-275):
```python
# Row 4: Production signals (7 subplots)
signal_names = [
    'msp_uncertainty',
    'predictive_entropy',
    'mutual_info',
    'inverse_coherence',
    'dominance',
    'inverse_mass',
    'inverse_logit_magnitude'
]
```

**Fixed**:
```python
from uqlab.shared.types import SIGNAL_NAMES

# Row 4: Production signals (7 subplots)
# Use centralized signal names from shared.types
for idx, signal_name in enumerate(SIGNAL_NAMES):
    ax_sig = fig.add_subplot(gs[3, idx])
    plot_signal_with_accuracy(...)
```

#### Priority 2: Remove Duplicates

**Files to update**:
1. `evaluation/benchmarks/visualization.py` - Import `SIGNAL_NAMES`
2. `results_io.py` - Remove duplicate, import from `shared.types`
3. `shared/notebook_utils/signals.py` - Remove duplicate, import from `shared.types`

#### Priority 3: Legacy Code (Document Only)

**Files in `scripts/legacy/`** - Add comment pointing to canonical source

---

## 📝 Implementation Plan

### Phase 1: Fix Active Visualization Code ✅

1. Update `uq_benchmarks.py` to import `SIGNAL_NAMES`
2. Remove hardcoded list
3. Test visualization renders correctly

### Phase 2: Consolidate Duplicates

1. Update `results_io.py` to import from `shared.types`
2. Update `notebook_utils/signals.py` to import from `shared.types`
3. Update `benchmarks/visualization.py` to import from `shared.types`

### Phase 3: Documentation

1. Add docstring to `shared/types.py::SIGNAL_NAMES` explaining it's canonical
2. Add comment in removed locations pointing to canonical source
3. Update this document with results

---

## 🎓 Teaching Moment: When to Centralize

### Always Centralize

✅ **Constants that define system behavior**:
- Signal names (our case)
- Metric names
- Configuration keys
- API endpoints
- Database table names

✅ **Lists that are iterated over**:
- Signal names for plotting
- Metric columns for analysis
- Feature names for ML

✅ **Enums and categorical values**:
- Status codes
- Error types
- Classification labels

### Sometimes Centralize

⚠️ **Context-specific configurations**:
- UI-specific display names (may differ from internal names)
- Test fixtures (may need variations)
- Example data (may be simplified)

### Don't Centralize

❌ **Truly local variables**:
- Loop counters
- Temporary calculations
- Function-specific logic

---

## 🔍 How to Check for Centralization Opportunities

### 1. Search for Patterns

```bash
# Find hardcoded lists
rg "signal_names\s*=\s*\[" --type py

# Find string literals that look like constants
rg "'msp_uncertainty'.*'predictive_entropy'" --type py
```

### 2. Look for Repetition

If you see the same list in 2+ files → **centralize it**

### 3. Ask These Questions

- ❓ "If I add a new signal, how many files must I update?"
  - Answer should be: **ONE**
  
- ❓ "Where is the authoritative definition?"
  - Should have a clear answer
  
- ❓ "Can this list change independently in different contexts?"
  - If NO → centralize
  - If YES → maybe keep separate (but document why)

---

## 📊 Impact Analysis

### Before Fix

**Locations with signal names**: 8+
**Maintenance burden**: HIGH (must update 8+ files)
**Bug risk**: HIGH (easy to miss one location)
**Consistency**: LOW (lists may drift apart)

### After Fix

**Locations with signal names**: 1 (canonical source)
**Maintenance burden**: LOW (update once)
**Bug risk**: LOW (impossible to have inconsistency)
**Consistency**: HIGH (guaranteed same everywhere)

---

## ✅ Verification Checklist

After implementing fixes:

- [ ] All visualization code imports from `shared.types`
- [ ] No hardcoded signal name lists in active code
- [ ] Tests pass
- [ ] Visualizations render correctly
- [ ] Documentation updated
- [ ] Legacy code has comments pointing to canonical source

---

## 🎯 Key Takeaways

1. **Define once, import everywhere** - The golden rule
2. **Search before creating** - Check if constant already exists
3. **Centralize early** - Easier to centralize than to refactor later
4. **Document the source** - Make it clear where the canonical definition lives
5. **Use type hints** - Help IDEs and developers find the source

---

**Status**: 📋 Analysis complete, ready for implementation  
**Next Step**: Fix `uq_benchmarks.py` to import `SIGNAL_NAMES`

---

*Made with Bob - Teaching best practices through real examples*