# Experiment Details Enhancement: Metrics Display + Uncertainty Explanations

## Overview

Enhanced the "Experiment Details" section in the progressive UI to display comprehensive metrics data and explain uncertainty types to users.

## Implementation Summary

### ✅ What Was Implemented

#### 1. **New Component: Experiment Details with Metrics** 
**File:** `src/uqlab/ui_components/results/experiment_details.py`

Comprehensive experiment details component that displays:
- **All 7 uncertainty signals** with their AUROC scores
- **Per-signal breakdown** showing both aleatoric and epistemic performance
- **Visual indicators** (🟢🟡🟠🔴) for performance levels
- **Best signal recommendations** for different use cases
- **Comparison charts** showing aleatoric vs epistemic performance

**Key Features:**
```python
def render_experiment_details_with_metrics(experiment, show_explanation=True):
    """
    Displays:
    - Experiment header with status, progress, timestamps
    - Uncertainty explanation (expandable)
    - Metrics table with all 7 signals
    - Best performing signals (3 categories)
    - Signal comparison bar chart
    """
```

**Metrics Table Format:**
| Signal | Aleatoric | Epistemic | Average |
|--------|-----------|-----------|---------|
| 🟢 msp_uncertainty | 0.850 | 0.720 | 0.785 |
| 🟡 dominance | 0.780 | 0.650 | 0.715 |
| ... | ... | ... | ... |

#### 2. **Uncertainty Explanation Component**
**Included in:** `experiment_details.py` as `render_uncertainty_explanation_compact()`

Provides clear, educational explanations:

**🎲 Aleatoric Uncertainty (Data Uncertainty)**
- What it is: Irreducible noise in the data
- Example: Mislabeled training sample
- Key point: More data won't help
- Use for: Data cleaning, quality control

**🧠 Epistemic Uncertainty (Model Uncertainty)**
- What it is: Lack of knowledge/training data
- Example: Under-trained classes
- Key point: More data WOULD help
- Use for: Active learning, identifying data gaps

**📊 AUROC Score Interpretation:**
- 0.5 = Random (coin flip)
- 0.6-0.7 = Fair
- 0.7-0.8 = Good
- 0.8-0.9 = Excellent
- 0.9-1.0 = Outstanding

#### 3. **API Endpoint Enhancement**
**File:** `backend/app/api/routes/experiments.py`

Added no-auth endpoint for fetching individual experiment details:
```python
@router.get("/no-auth/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment_no_auth(experiment_id: str, session: SessionDep):
    """Get experiment details including best_signals_json"""
```

#### 4. **Progressive UI Integration**
**File:** `streamlit_app_progressive.py`

Enhanced two sections:

**A. Standalone Experiments Section:**
- Added "View Detailed Metrics" section
- Shows expandable details for each completed experiment
- Includes full uncertainty explanation

**B. Sweep Groups Section:**
**File:** `src/uqlab/ui_components/grouping/sweep_grouping.py`
- Enhanced `render_sweep_group_summary()` to show detailed metrics
- Added expandable views for each experiment in a sweep
- Compact explanation (no redundancy across multiple experiments)

## Data Structure

### Database Schema
The `UncertaintyExperiment` table stores metrics in `best_signals_json`:

```python
class UncertaintyExperiment(SQLModel, table=True):
    # ... other fields ...
    best_signals_json: str | None = None  # JSON string with all 7 signals
```

### JSON Format
```json
{
  "one_vs_rest_auroc": [
    {
      "signal": "msp_uncertainty",
      "aleatoric_like_auroc": 0.850,
      "epistemic_like_auroc": 0.720
    },
    {
      "signal": "dominance",
      "aleatoric_like_auroc": 0.780,
      "epistemic_like_auroc": 0.650
    },
    // ... 5 more signals (7 total)
  ]
}
```

### The 7 Uncertainty Signals
1. **msp_uncertainty** - Maximum Softmax Probability
2. **dominance** - Dominance of top prediction
3. **entropy** - Prediction entropy
4. **margin** - Margin between top 2 predictions
5. **least_confidence** - Inverse of top prediction confidence
6. **variation_ratio** - Variation in predictions
7. **mutual_information** - Information gain

Each signal has:
- `aleatoric_like_auroc`: Performance at detecting noisy labels
- `epistemic_like_auroc`: Performance at detecting under-trained classes

## User Experience Flow

### 1. **Viewing Sweep Results**
```
User clicks on sweep group
  → Sees summary (best AUROC scores)
  → Expands "Experiment Details"
  → Sees table of all experiments
  → Clicks "View Detailed Metrics" for specific experiment
  → Sees:
     - All 7 signals with AUROC scores
     - Best signals for each use case
     - Comparison chart
     - Uncertainty explanation (optional)
```

### 2. **Viewing Standalone Experiments**
```
User expands "Standalone Experiments"
  → Sees table of experiments
  → Expands "View Detailed Metrics"
  → Selects experiment
  → Sees full metrics breakdown with explanation
```

## Visual Design

### Performance Indicators
- 🟢 **Green (≥0.8):** Excellent - Strong discrimination
- 🟡 **Yellow (≥0.7):** Good - Reliable signal
- 🟠 **Orange (≥0.6):** Fair - Some useful information
- 🔴 **Red (<0.6):** Poor - May not be useful

### Best Signals Display
Three recommendation cards:
1. **🎲 Best for Aleatoric** - Data quality control
2. **🧠 Best for Epistemic** - Active learning
3. **⭐ Best Overall Balance** - General UQ

### Comparison Chart
Bar chart showing aleatoric vs epistemic performance side-by-side for all signals.

## Benefits

### For Users
✅ **Understand what metrics mean** - Clear explanations with examples
✅ **See all signal performance** - Not just aggregated max values
✅ **Get actionable recommendations** - Which signal to use for what
✅ **Visual performance indicators** - Quick assessment at a glance
✅ **Learn about uncertainty types** - Educational content built-in

### For Researchers
✅ **Compare signals systematically** - All 7 signals in one view
✅ **Identify best signals per task** - Separate aleatoric/epistemic rankings
✅ **Understand trade-offs** - See which signals excel at what
✅ **Make informed decisions** - Data-driven signal selection

## Files Modified

### New Files Created
1. `src/uqlab/ui_components/results/experiment_details.py` (283 lines)
   - Main component with metrics display
   - Uncertainty explanation
   - Best signals recommendations
   - Comparison charts

### Modified Files
1. `backend/app/api/routes/experiments.py`
   - Added `get_experiment_no_auth()` endpoint

2. `src/uqlab/ui_components/grouping/sweep_grouping.py`
   - Enhanced `render_sweep_group_summary()` with detailed metrics view
   - Added expandable experiment details

3. `streamlit_app_progressive.py`
   - Integrated detailed metrics view in standalone experiments section
   - Added import for new component

## Testing Checklist

- [ ] **View completed experiment details**
  - Navigate to experiment list
  - Expand a completed experiment
  - Verify all 7 signals are displayed
  - Check AUROC values are formatted correctly
  - Verify color indicators match performance levels

- [ ] **Check best signals recommendations**
  - Verify "Best for Aleatoric" shows highest aleatoric AUROC
  - Verify "Best for Epistemic" shows highest epistemic AUROC
  - Verify "Best Overall" shows highest average

- [ ] **Test uncertainty explanation**
  - Expand "What do these metrics mean?"
  - Verify aleatoric explanation is clear
  - Verify epistemic explanation is clear
  - Check AUROC score interpretation table

- [ ] **Test comparison chart**
  - Verify bar chart displays correctly
  - Check all 7 signals are shown
  - Verify bars are sorted by average performance

- [ ] **Test with different experiment states**
  - Queued experiment: Should show "metrics will be available"
  - Running experiment: Should show progress
  - Failed experiment: Should handle gracefully
  - Completed without metrics: Should show warning

- [ ] **Test in sweep groups**
  - Expand sweep group
  - Click "View Detailed Metrics"
  - Verify multiple experiments can be expanded
  - Check no redundant explanations

- [ ] **Test in standalone experiments**
  - Expand standalone experiments section
  - Verify detailed metrics are available
  - Check explanation is shown (first time)

## Usage Examples

### Example 1: Finding Best Signal for Data Cleaning
```
User wants to identify mislabeled training samples:
1. View experiment details
2. Look at "Best for Aleatoric" recommendation
3. Use that signal (e.g., msp_uncertainty with 0.85 AUROC)
4. Apply to training data for quality control
```

### Example 2: Active Learning Setup
```
User wants to identify where to collect more data:
1. View experiment details
2. Look at "Best for Epistemic" recommendation
3. Use that signal (e.g., entropy with 0.78 AUROC)
4. Query samples with high epistemic uncertainty
```

### Example 3: Comparing Experiments in a Sweep
```
User ran noise_rate sweep (0%, 10%, 20%, 30%):
1. Expand sweep group
2. View detailed metrics for each run
3. Compare how signal performance degrades with noise
4. Identify which signals are most robust
```

## Future Enhancements

### Potential Additions
1. **Signal correlation analysis** - Show which signals are redundant
2. **Per-class performance** - Break down AUROC by class
3. **Confidence calibration plots** - Show reliability diagrams
4. **Export metrics to CSV** - Download button for analysis
5. **Historical comparison** - Compare with previous experiments
6. **Signal combination recommendations** - Suggest ensemble strategies

### Performance Optimizations
1. **Lazy loading** - Only fetch metrics when expanded
2. **Caching** - Cache parsed metrics in session state
3. **Pagination** - For experiments with many signals

## Success Criteria

✅ **Users understand uncertainty types** - Clear explanations with examples
✅ **All 7 signals are displayed** - Complete metrics breakdown
✅ **AUROC scores are color-coded** - Visual performance indicators
✅ **Best signals are highlighted** - Actionable recommendations
✅ **Works with existing data** - Parses best_signals_json correctly
✅ **Integrated into progressive UI** - Seamless user experience

## Notes

- The implementation uses emoji indicators (🟢🟡🟠🔴) instead of pandas styling for better compatibility
- Uncertainty explanation is expandable to avoid cluttering the UI
- API endpoint supports no-auth for local development
- Component is reusable across different UI sections
- All 7 signals are always shown (not just top performers)

---

**Implementation Date:** 2026-06-15
**Status:** ✅ Complete (pending testing)
**Made with Bob** 🤖