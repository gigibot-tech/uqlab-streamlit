# Training Data Inspection Feature - Implementation Documentation

## 📋 Executive Summary

The training data inspection feature is **fully implemented and integrated** into the experiment details view. It provides comprehensive visualization and analysis of training data, including label flip statistics, per-class breakdowns, and sample-level inspection tables.

**Status:** ✅ **COMPLETE AND OPERATIONAL**

---

## 🗂️ Implementation Location

### Primary Module
**File:** `src/uqlab/ui_components/results/training_data_inspection.py`
- **Size:** 265 lines
- **Created:** June 15, 2024, 23:57
- **Status:** Fully implemented

### Integration Point
**File:** `src/uqlab/ui_components/results/results.py`
- **Line 16:** Import statement
- **Line 177:** Integration call within experiment details expander

### Exports
**File:** `src/uqlab/ui_components/results/__init__.py`
- Exports: `render_training_data_stats`, `parse_training_data_stats`, `generate_training_stats_from_config`, `CIFAR10_CLASSES`

**File:** `src/uqlab/ui_components/__init__.py`
- Re-exports all functions for top-level access

---

## 🔧 Core Functions

### 1. `parse_training_data_stats(experiment_id: str) -> Optional[Dict]`
**Purpose:** Parse training data statistics from experiment results files

**Location:** Lines 20-97 in `training_data_inspection.py`

**Functionality:**
- Searches multiple possible file locations:
  - `data/experiments/{experiment_id}/results/training_data.csv`
  - `data/experiments/{experiment_id}/results/per_sample_signals.csv`
  - `/tmp/uqlab_experiments/{experiment_id}/results/training_data.csv`
  - `/tmp/uqlab_experiments/{experiment_id}/results/per_sample_signals.csv`
- Validates required columns: `clean_label`, `noisy_label`
- Calculates overall statistics (total, clean, noisy samples, noise rate)
- Computes per-class statistics for all 10 CIFAR-10 classes
- Returns full dataframe for table display

**Return Structure:**
```python
{
    'total_samples': int,
    'clean_samples': int,
    'noisy_samples': int,
    'noise_rate': float,
    'class_stats': [
        {
            'class_idx': int,
            'class_name': str,
            'total_samples': int,
            'clean_samples': int,
            'noisy_samples': int,
            'noise_rate': float
        },
        # ... for all 10 classes
    ],
    'samples_df': DataFrame  # Full dataframe
}
```

### 2. `render_training_data_stats(experiment_id: str) -> None`
**Purpose:** Render complete training data inspection UI

**Location:** Lines 100-216 in `training_data_inspection.py`

**UI Components:**
1. **Header:** "📊 Training Data Inspection"
2. **Overall Statistics:** 4-column metrics display
   - Total Samples
   - Clean Samples
   - Noisy Samples
   - Noise Rate (percentage)
3. **Per-Class Statistics:** Scrollable table (400px height)
   - Class name
   - Total samples
   - Clean samples
   - Noisy samples
   - Noise percentage
4. **Sample-Level Inspection:** Interactive table with filters
   - Columns: Sample Index, Clean Label, Clean Class, Noisy Label, Noisy Class, Is Noisy
   - Filter by: Show only noisy samples (checkbox)
   - Filter by: Clean class (dropdown)
   - Shows filtered count
   - Scrollable (400px height)
   - CSV download button

### 3. `generate_training_stats_from_config(experiment_config: Dict) -> Optional[Dict]`
**Purpose:** Fallback function to estimate statistics from config when actual data files are unavailable

**Location:** Lines 219-262 in `training_data_inspection.py`

**Functionality:**
- Extracts configuration parameters
- Calculates estimated sample counts
- Returns simplified statistics with `estimated: True` flag

### 4. `CIFAR10_CLASSES` Constant
**Location:** Lines 14-17 in `training_data_inspection.py`

**Value:**
```python
["airplane", "automobile", "bird", "cat", "deer",
 "dog", "frog", "horse", "ship", "truck"]
```

---

## 🔗 Integration Details

### Where It's Called
**File:** `src/uqlab/ui_components/results/results.py`
**Function:** `_render_experiment_detail()`
**Line:** 177

```python
# Training data inspection section
st.markdown("---")
render_training_data_stats(exp['id'])
```

### Context
The training data inspection is rendered:
- **Inside** the experiment details expander
- **After** the basic info and configuration sections
- **Before** the watsonx.ai export section
- **Separated** by horizontal rules (`---`)

### Display Conditions
- Always rendered for all experiments (queued, running, completed, failed)
- Shows info message if data not available: "Training data statistics not available for this experiment"
- Gracefully handles missing files

---

## 📊 UI Layout Structure

```
Experiment Details Expander
├── Basic Info & Configuration (2 columns)
├── Results Data (if available)
├── ─────────────────────────────
├── 📊 Training Data Inspection
│   ├── Overall Statistics (4 metrics)
│   ├── Per-Class Statistics (table)
│   └── Sample-Level Inspection
│       ├── Filters (checkbox + dropdown)
│       ├── Sample count caption
│       ├── Data table (scrollable)
│       └── Download CSV button
├── ─────────────────────────────
├── 🚀 Export to watsonx.ai (if completed)
└── 🗑️ Delete Experiment
```

---

## 🎯 Features Implemented

### ✅ Overall Statistics
- [x] Total samples count
- [x] Clean samples count
- [x] Noisy samples count
- [x] Noise rate percentage
- [x] 4-column metric display

### ✅ Per-Class Statistics
- [x] All 10 CIFAR-10 classes
- [x] Class name display
- [x] Total samples per class
- [x] Clean samples per class
- [x] Noisy samples per class
- [x] Noise rate per class
- [x] Formatted percentage display
- [x] Scrollable table (400px)

### ✅ Sample-Level Inspection
- [x] Sample index column
- [x] Clean label (numeric)
- [x] Clean class (name)
- [x] Noisy label (numeric)
- [x] Noisy class (name)
- [x] Is Noisy flag
- [x] Filter by noisy samples only
- [x] Filter by clean class
- [x] Filtered count display
- [x] Scrollable table (400px)
- [x] CSV download button
- [x] Unique keys for widgets (prevents conflicts)

### ✅ Error Handling
- [x] Multiple file path attempts
- [x] Graceful handling of missing files
- [x] Info message when data unavailable
- [x] Exception handling with error display
- [x] Column validation

### ✅ Export Functionality
- [x] Properly exported from results package
- [x] Re-exported from main ui_components package
- [x] Available for import in main app

---

## 🔍 Data File Locations

The feature searches for training data in the following locations (in order):

1. `data/experiments/{experiment_id}/results/training_data.csv`
2. `data/experiments/{experiment_id}/results/per_sample_signals.csv`
3. `/tmp/uqlab_experiments/{experiment_id}/results/training_data.csv`
4. `/tmp/uqlab_experiments/{experiment_id}/results/per_sample_signals.csv`

### Required CSV Columns
- `clean_label` (required)
- `noisy_label` (required)
- `is_noisy` (optional - will be inferred if missing)
- `dataset_index` or `index` or `sample_index` (optional - for display)

---

## 🎨 UI Design Patterns

### Metrics Display
- Uses `st.metric()` for clean, professional display
- 4-column layout for overall statistics
- Formatted numbers with thousands separators
- Percentage formatting for rates

### Tables
- Uses `st.dataframe()` with `use_container_width=True`
- Fixed height (400px) for scrollability
- `hide_index=True` for cleaner display
- Formatted columns with proper headers

### Filters
- Checkbox for binary filter (show only noisy)
- Selectbox for categorical filter (class selection)
- Unique keys using experiment_id to prevent conflicts
- Caption showing filtered count

### Download
- `st.download_button()` for CSV export
- Filename includes experiment ID (first 8 chars)
- Proper MIME type (`text/csv`)
- Unique key to prevent conflicts

---

## 🚀 How to Access in UI

1. **Navigate to Results Section**
   - Open the Streamlit app
   - Go to the "Results" or "Experiments" section

2. **Expand Experiment Details**
   - Click on any experiment expander
   - Look for the status emoji (⏳ ⏳ ✅ ❌)

3. **Scroll to Training Data Section**
   - After basic info and configuration
   - Look for "📊 Training Data Inspection" header

4. **Interact with Features**
   - View overall statistics at the top
   - Scroll through per-class statistics table
   - Use filters to explore sample-level data
   - Download filtered data as CSV

---

## 📝 Code Quality

### Strengths
- ✅ Well-documented with docstrings
- ✅ Type hints for all functions
- ✅ Comprehensive error handling
- ✅ Modular design (separate functions)
- ✅ Proper imports and exports
- ✅ Unique widget keys (no conflicts)
- ✅ Graceful degradation (missing data)
- ✅ Multiple file path fallbacks

### Best Practices
- ✅ Uses Streamlit native components
- ✅ Follows project structure conventions
- ✅ Proper separation of concerns
- ✅ Reusable constants (CIFAR10_CLASSES)
- ✅ Clean, readable code
- ✅ Consistent formatting

---

## 🐛 Known Limitations

1. **CIFAR-10 Specific**
   - Hardcoded for 10 classes
   - Class names are CIFAR-10 specific
   - Would need modification for other datasets

2. **File Path Assumptions**
   - Assumes specific directory structure
   - Limited to CSV format
   - No support for other data formats

3. **No Real-time Updates**
   - Requires page refresh to see new data
   - No streaming updates during training

---

## 🔮 Future Enhancements (Optional)

### Potential Improvements
- [ ] Support for other datasets (ImageNet, custom)
- [ ] Configurable class names
- [ ] Real-time updates during training
- [ ] More advanced filtering options
- [ ] Visualization of sample images
- [ ] Confusion matrix for label flips
- [ ] Statistical tests for noise patterns
- [ ] Export to multiple formats (JSON, Excel)

---

## ✅ Verification Checklist

- [x] Module exists and is accessible
- [x] Functions are properly implemented
- [x] Integration point is correct
- [x] Exports are configured
- [x] UI components render correctly
- [x] Error handling is robust
- [x] Documentation is complete
- [x] Code follows best practices

---

## 📚 Related Files

### Implementation Files
- `src/uqlab/ui_components/results/training_data_inspection.py` (main module)
- `src/uqlab/ui_components/results/results.py` (integration)
- `src/uqlab/ui_components/results/__init__.py` (exports)
- `src/uqlab/ui_components/__init__.py` (re-exports)

### Related Components
- `src/uqlab/ui_components/results/experiment_details.py` (enhanced metrics display)
- `src/uqlab/ui_components/visualization/` (other visualization components)

---

## 🎓 Usage Example

```python
from uqlab.ui_components import render_training_data_stats, parse_training_data_stats

# Parse statistics
stats = parse_training_data_stats(experiment_id="abc123")

if stats:
    print(f"Total samples: {stats['total_samples']}")
    print(f"Noise rate: {stats['noise_rate']:.2%}")
    
    # Render UI
    render_training_data_stats(experiment_id="abc123")
else:
    print("Training data not available")
```

---

## 📞 Support

For questions or issues related to the training data inspection feature:
1. Check this documentation first
2. Review the source code in `training_data_inspection.py`
3. Check experiment logs for data file availability
4. Verify CSV file format matches expected structure

---

**Document Version:** 1.0  
**Last Updated:** June 15, 2024  
**Status:** Complete and Verified  
**Author:** Bob (AI Assistant)

---

*Made with Bob* 🤖