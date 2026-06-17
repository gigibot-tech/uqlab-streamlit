# Training Data Inspection in Progressive UI

## Overview

The training data inspection feature has been successfully integrated into the Progressive Streamlit App (`streamlit_app_progressive.py`). Users can now view detailed training data statistics including label flips, clean vs noisy samples, and per-class breakdowns directly in the progressive UI.

## Implementation Summary

### Files Modified

1. **`streamlit_app_progressive.py`**
   - Added imports for training data inspection functions
   - Added standalone "Training Data Inspection" section in results panel
   - Integrated with existing experiment results display

2. **`src/uqlab/ui_components/results/experiment_details.py`**
   - Added imports for training data inspection
   - Added `_render_training_data_section()` function
   - Integrated training data inspection into detailed experiment view

### Features Added

#### 1. Standalone Training Data Inspection Section

**Location**: In the main results panel, after standalone experiments and before batch experiments

**Features**:
- Dropdown selector to choose which completed experiment to inspect
- Only shows experiments that have training data available
- Displays in an expandable section (expanded by default)
- Shows informative message when no training data is available

**Code Location**: Lines 333-365 in `streamlit_app_progressive.py`

#### 2. Integrated Training Data in Experiment Details

**Location**: Within the detailed metrics view for each experiment

**Features**:
- Appears after uncertainty metrics in experiment details
- Shown in a collapsible expander (collapsed by default)
- Automatically detects if training data is available
- Shows helpful message if data is not available

**Code Location**: Lines 99-119 in `experiment_details.py`

## User Experience

### Accessing Training Data Inspection

Users can access training data inspection in two ways:

#### Option 1: Standalone Section (Main Results Panel)

1. Navigate to the results section (appears after Step 4 is complete)
2. Scroll to "📊 Training Data Inspection" section
3. Select an experiment from the dropdown
4. View statistics in the expanded panel

#### Option 2: Experiment Details View

1. Navigate to "🧪 Individual Experiments" section
2. Expand "📋 View X Standalone Experiments"
3. Expand "🔬 [Experiment Name] - Detailed Metrics"
4. Scroll to bottom and expand "📊 Training Data Inspection"

### What Users See

When training data is available, users see:

1. **Overall Statistics**
   - Total Samples
   - Clean Samples
   - Noisy Samples
   - Noise Rate (%)

2. **Per-Class Statistics Table**
   - Class name
   - Total samples per class
   - Clean samples per class
   - Noisy samples per class
   - Noise percentage per class

3. **Sample-Level Inspection**
   - Scrollable table with all training samples
   - Columns: Sample Index, Clean Label, Clean Class, Noisy Label, Noisy Class, Is Noisy
   - Filter options:
     - Show only noisy samples checkbox
     - Filter by clean class dropdown
   - Download button for filtered data as CSV

## Technical Details

### Data Source

Training data is loaded from experiment results files:
- Primary: `data/experiments/{experiment_id}/results/training_data.csv`
- Fallback: `data/experiments/{experiment_id}/results/per_sample_signals.csv`
- Alternative paths in `/tmp/uqlab_experiments/` are also checked

### Required Columns

The training data CSV must contain:
- `clean_label`: Original correct label
- `noisy_label`: Label used for training (may be flipped)
- `is_noisy` (optional): Boolean flag, inferred if missing

### Integration Points

The feature integrates with:
- `render_experiment_results_panel()`: Main results display function
- `render_experiment_details_with_metrics()`: Detailed experiment view
- `parse_training_data_stats()`: Data parsing utility
- `render_training_data_stats()`: UI rendering component

## Benefits

1. **Transparency**: Users can see exactly what data was used for training
2. **Quality Control**: Easy identification of noisy samples and label flips
3. **Analysis**: Per-class statistics help understand model behavior
4. **Export**: CSV download enables further analysis in external tools
5. **Accessibility**: Available in both summary and detailed views

## Future Enhancements

Potential improvements:
1. Add visualization charts (bar charts for per-class noise rates)
2. Add comparison view for multiple experiments
3. Add filtering by noise type (if using CIFAR-10N)
4. Add sample image preview (if image paths are available)
5. Add sidebar navigation anchor for quick access

## Testing

To test the feature:

1. **Run the progressive app**:
   ```bash
   cd uqlab-streamlit
   streamlit run streamlit_app_progressive.py
   ```

2. **Create and run an experiment** with training data saving enabled

3. **Navigate to results section** after experiment completes

4. **Check both access points**:
   - Standalone "Training Data Inspection" section
   - Experiment details expander

5. **Verify all features**:
   - Overall statistics display correctly
   - Per-class table shows accurate data
   - Sample-level table is scrollable
   - Filters work (noisy only, class filter)
   - CSV download works

## Troubleshooting

### "Training data statistics not available"

**Cause**: Training data file not found

**Solutions**:
- Ensure experiment saves training data during execution
- Check file paths match expected locations
- Verify experiment completed successfully

### Import errors

**Cause**: Module path issues

**Solutions**:
- Ensure `src/` is on PYTHONPATH
- Check all imports are correct
- Restart Streamlit app

### Empty statistics

**Cause**: CSV file missing required columns

**Solutions**:
- Verify CSV has `clean_label` and `noisy_label` columns
- Check CSV is not corrupted
- Ensure experiment used correct data saving format

## Code Examples

### Adding Training Data to New Views

```python
from uqlab.ui_components.results.training_data_inspection import (
    render_training_data_stats,
    parse_training_data_stats
)

# Check if data is available
experiment_id = "your-experiment-id"
train_stats = parse_training_data_stats(experiment_id)

if train_stats:
    # Render the full UI
    render_training_data_stats(experiment_id)
else:
    st.info("Training data not available")
```

### Accessing Statistics Programmatically

```python
from uqlab.ui_components.results.training_data_inspection import parse_training_data_stats

experiment_id = "your-experiment-id"
stats = parse_training_data_stats(experiment_id)

if stats:
    print(f"Total samples: {stats['total_samples']}")
    print(f"Noise rate: {stats['noise_rate']:.2%}")
    
    # Access per-class stats
    for class_stat in stats['class_stats']:
        print(f"{class_stat['class_name']}: {class_stat['noise_rate']:.2%} noisy")
    
    # Access full dataframe
    df = stats['samples_df']
    noisy_samples = df[df['is_noisy'] == True]
```

## Conclusion

The training data inspection feature is now fully integrated into the Progressive Streamlit App, providing users with comprehensive visibility into their training data. The feature is accessible, informative, and enhances the overall experiment analysis workflow.

---

**Implementation Date**: 2026-06-15  
**Author**: Bob (AI Assistant)  
**Status**: ✅ Complete and Ready for Use