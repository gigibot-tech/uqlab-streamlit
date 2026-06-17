# Phase 5: Streamlit UI - Complete ✅

## Overview

Phase 5 successfully adds a new "UQ Benchmarks" tab to the Streamlit dashboard, providing a user-friendly interface for running uncertainty quantification benchmarks using the new `uq_benchmarks` package.

## What Was Built

### 1. New UI Component (`ui_components/uq_benchmarks.py` - 330 lines)

A complete Streamlit interface with three sub-tabs:

#### Sub-Tab 1: 🎯 Single Run
**Purpose**: Configure and run individual benchmark experiments

**Features**:
- **Method Selection**: Dropdown to choose UQ method (Gaussian Logits, etc.)
- **Method Info Display**: Shows description and framework
- **Dataset Configuration**:
  - Epistemic: Under-supported classes, samples per class
  - Aleatoric: Label noise rate
  - Test mode toggle for quick experiments
- **Training Configuration**: Epochs, batch size, learning rate
- **Evaluation Configuration**: MC dropout passes
- **Results Display**: 
  - Metrics: Accuracy, aleatoric uncertainty, epistemic uncertainty
  - Timing: Training time, evaluation time
  - Full configuration in expandable section

**User Flow**:
```
1. Select UQ method → 2. Configure dataset → 3. Set training params → 
4. Click "Run Benchmark" → 5. View results
```

#### Sub-Tab 2: 📊 Parameter Sweep
**Purpose**: Run multiple experiments with varying parameters

**Features**:
- Method selection
- Parameter to sweep (noise_rate, under_train_per_class, etc.)
- Range configuration (start, end, step)
- Automatic calculation of number of runs
- Base configuration for non-swept parameters

**Status**: UI complete, backend integration coming in Phase 6

#### Sub-Tab 3: 📋 Results
**Purpose**: View and compare benchmark results

**Features** (Coming in Phase 6):
- Table of all benchmark results
- Filter by method, date, user
- Compare multiple runs
- Export to CSV
- Visualize uncertainty trends

### 2. Main App Integration (`streamlit_app.py`)

**Changes Made**:
1. **Import**: Added `from ui_components.uq_benchmarks import render_uq_benchmarks_tab`
2. **New Tab**: Added "🔬 UQ Benchmarks" to tabs list
3. **Tab Content**: Renders the new UI component

**Code**:
```python
# Import (line 40)
from ui_components.uq_benchmarks import render_uq_benchmarks_tab

# Tab definition (line 174)
unified_tab, single_tab, batch_tab, batch_2d_tab, model_tab, benchmarks_tab = st.tabs([
    "🚀 Unified Builder",
    "Single Experiment",
    "Batch Experiments (1D)",
    "Batch Experiments (2D Grid)",
    "🎯 Model Selector",
    "🔬 UQ Benchmarks"  # NEW
])

# Tab content (line 1011)
with benchmarks_tab:
    render_uq_benchmarks_tab(API_BASE_URL, get_headers)
```

## Design Decisions

### 1. ✅ Separate Tab (Not Integrated)

**Why a new tab?**
- **Clean separation**: New approach doesn't interfere with existing workflows
- **Easy comparison**: Users can compare old vs new methods side-by-side
- **Backward compatible**: Existing tabs unchanged
- **Future-proof**: Easy to add more UQ methods without cluttering UI

### 2. ✅ Three Sub-Tabs Structure

**Why sub-tabs?**
- **Organized workflow**: Single run → Sweep → Results
- **Progressive disclosure**: Show only relevant options
- **Scalability**: Easy to add more sub-tabs (e.g., "Comparison", "Export")

### 3. ✅ Method-Agnostic Interface

**Why generic configuration?**
- **Flexibility**: Works with any UQ method (Gaussian Logits, IT, DualXDA)
- **Consistency**: Same UI for all methods
- **Extensibility**: New methods just need backend implementation

### 4. ✅ Test Mode Toggle

**Why test mode?**
- **Quick iteration**: Smaller dataset for rapid testing
- **Development**: Faster feedback during development
- **Production**: Full dataset for real experiments

### 5. ✅ Real-time API Integration

**How it works**:
```python
# Fetch available methods
methods_info = fetch_available_methods(api_base_url, get_headers_func)

# Run benchmark
response = requests.post(
    f"{api_base_url}/api/v1/uq-benchmarks/single",
    json=payload,
    timeout=600  # 10 minutes
)
```

## User Experience

### Single Run Workflow

1. **Navigate to Tab**
   - Click "🔬 UQ Benchmarks" tab
   - See introduction and available methods

2. **Select Method**
   - Choose from dropdown (e.g., "gaussian_logits")
   - View method description and framework

3. **Configure Dataset**
   - **Epistemic**: Select under-supported classes (e.g., [3, 5])
   - **Aleatoric**: Set noise rate (e.g., 0.2 = 20%)
   - Toggle test mode for quick experiments

4. **Set Training Parameters**
   - Epochs: 5-10 for testing, 20+ for production
   - Batch size: 32 (default)
   - Learning rate: 0.001 (default)

5. **Configure Evaluation**
   - MC passes: 10 for testing, 20+ for production

6. **Run Benchmark**
   - Click "🚀 Run Benchmark"
   - Wait for completion (progress spinner)
   - View results

7. **Analyze Results**
   - See accuracy, uncertainties, timing
   - Expand configuration for details

### Example Configuration

**Quick Test** (2-3 minutes):
```
Method: gaussian_logits
Under-supported: [3, 5]
Under samples: 50
Regular samples: 300
Noise rate: 0.2
Test mode: ✓
Epochs: 5
MC passes: 10
```

**Production Run** (10-15 minutes):
```
Method: gaussian_logits
Under-supported: [3, 5]
Under samples: 50
Regular samples: 500
Noise rate: 0.2
Test mode: ✗
Epochs: 20
MC passes: 30
```

## API Integration

### Endpoints Used

1. **GET `/api/v1/uq-benchmarks/methods`**
   - Fetches available UQ methods
   - Shows which methods are installed
   - Displays method info (name, description, framework)

2. **POST `/api/v1/uq-benchmarks/single`**
   - Runs single benchmark experiment
   - Accepts full configuration
   - Returns results with timing

3. **POST `/api/v1/uq-benchmarks/label-noise-sweep`** (Phase 6)
   - Runs parameter sweep
   - Generates multiple experiments
   - Returns aggregated results

### Request/Response Example

**Request**:
```json
{
  "method": "gaussian_logits",
  "dataset_config": {
    "under_supported_classes": [3, 5],
    "under_train_per_class": 50,
    "regular_train_per_class": 300,
    "noise_rate": 0.2,
    "test_mode": true,
    "seed": 42
  },
  "training_config": {
    "epochs": 5,
    "batch_size": 32,
    "learning_rate": 0.001
  },
  "evaluation_config": {
    "mc_passes": 10
  }
}
```

**Response**:
```json
{
  "method": "gaussian_logits",
  "accuracy": 0.85,
  "aleatoric_uncertainty": 0.15,
  "epistemic_uncertainty": 0.08,
  "training_time": 45.2,
  "evaluation_time": 12.3,
  "config": { ... }
}
```

## Error Handling

### No Methods Available
```python
if not available_methods:
    st.warning("⚠️ No UQ methods are currently available.")
    st.code("pip install uq-benchmarks[keras]")
    return
```

### API Request Failed
```python
except requests.exceptions.RequestException as e:
    st.error(f"❌ Benchmark failed: {str(e)}")
    if hasattr(e, 'response') and e.response is not None:
        st.error(f"Response: {e.response.text}")
```

### Timeout Handling
```python
response = requests.post(
    url,
    json=payload,
    timeout=600  # 10 minutes for long-running experiments
)
```

## Backward Compatibility

### ✅ Zero Breaking Changes

**Existing tabs unchanged**:
- 🚀 Unified Builder: Works as before
- Single Experiment: Works as before
- Batch Experiments (1D): Works as before
- Batch Experiments (2D Grid): Works as before
- 🎯 Model Selector: Works as before

**New tab added**:
- 🔬 UQ Benchmarks: New functionality

**Users can**:
- Continue using existing workflows
- Explore new benchmarks at their own pace
- Compare old vs new approaches

## Testing Instructions

### 1. Start Backend
```bash
cd uqlab-streamlit/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Streamlit
```bash
cd uqlab-streamlit
streamlit run streamlit_app.py
```

### 3. Navigate to Tab
- Open http://localhost:8501
- Click "🔬 UQ Benchmarks" tab

### 4. Run Quick Test
- Select "gaussian_logits"
- Keep default settings
- Enable "Test mode"
- Click "🚀 Run Benchmark"
- Wait 2-3 minutes
- View results

### 5. Verify Results
- Accuracy should be ~0.7-0.9
- Aleatoric uncertainty should be ~0.1-0.2
- Epistemic uncertainty should be ~0.05-0.15
- Training time should be ~30-60s
- Evaluation time should be ~10-20s

## Known Limitations

### Phase 5 Scope
- ✅ Single run UI complete
- ✅ Parameter sweep UI complete
- ⏳ Results display (Phase 6)
- ⏳ Visualization (Phase 6)
- ⏳ Export functionality (Phase 6)

### Future Enhancements (Phase 6)
1. **Results Table**: Display all benchmark results
2. **Filtering**: By method, date, user
3. **Comparison**: Side-by-side comparison
4. **Visualization**: Charts for uncertainty trends
5. **Export**: CSV/JSON export

## Files Modified/Created

### Created:
1. **`ui_components/uq_benchmarks.py`** (330 lines)
   - Complete UI component for benchmarks tab
   - Three sub-tabs: Single Run, Sweep, Results
   - API integration and error handling

### Modified:
1. **`streamlit_app.py`** (3 changes)
   - Added import for new UI component
   - Added "🔬 UQ Benchmarks" to tabs list
   - Added tab content rendering

## Next Steps (Phase 6)

### Benchmark Visualization
1. **Results Table**
   - Query benchmark results from database
   - Display in sortable/filterable table
   - Show method, accuracy, uncertainties, timing

2. **Comparison View**
   - Select multiple results
   - Side-by-side comparison
   - Highlight differences

3. **Charts**
   - Uncertainty vs noise rate
   - Accuracy vs dataset size
   - Training time vs epochs

4. **Export**
   - CSV export for analysis
   - JSON export for archival
   - Copy to clipboard

## Summary

✅ **Phase 5 Complete**: Streamlit UI is production-ready

**Key Achievements**:
- New "UQ Benchmarks" tab with clean separation
- Complete single run interface
- Parameter sweep UI (backend integration in Phase 6)
- Real-time API integration
- Error handling and user feedback
- Zero breaking changes to existing tabs

**User Benefits**:
- Easy-to-use interface for running benchmarks
- No need to write code
- Immediate visual feedback
- Test mode for quick iteration
- Production mode for real experiments

**Total Code**: ~335 lines of Streamlit UI code

**Next Phase**: Add visualization and results display (Phase 6)