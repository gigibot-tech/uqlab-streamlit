# Progressive Disclosure Streamlit App

## Overview

`streamlit_app_progressive.py` is a redesigned experiment configuration interface that uses **progressive disclosure** to reduce cognitive load and guide users through the experiment setup process step-by-step.

## Key Features

### 🎯 Progressive Disclosure Pattern
- **One step at a time**: Only shows the current configuration step
- **Explicit continuation**: Users must click "Continue" to proceed
- **No defaults**: Forces deliberate choices (inspired by MLflow UI)
- **Visual feedback**: Completed steps show as collapsed summaries
- **Easy editing**: Click "Edit" on any completed step to modify

### 📊 5-Step Workflow

#### Step 1: Dataset Selection
- Choose dataset (CIFAR-10)
- Select noise type (none, worse_label, random_label1, random_label2)
- View dataset statistics
- **Stops until dataset is selected**

#### Step 2: Training Setup
- **Option A**: Train new model
  - Select architecture (DINOv2, ResNet)
  - Configure hyperparameters (epochs, learning rate, batch size)
- **Option B**: Use existing checkpoint
  - Select from completed experiments
- **Stops until training mode is configured**

#### Step 3: Uncertainty Configuration
- **Epistemic Uncertainty** (left column)
  - Enable/disable dataset size sweep
  - Configure under-supported classes (random or manual)
  - Set samples per class
- **Aleatoric Uncertainty** (right column)
  - Use dataset noise or add custom noise
  - Configure noise rate
- **Dataset preview** shows resulting training distribution
- **Stops until uncertainty is configured**

#### Step 4: Evaluation Setup
- Configure evaluation pool size
- Set MC dropout passes
- Select uncertainty signals:
  - Epistemic: inverse_mass, dominance, inverse_logit_magnitude
  - Aleatoric: inverse_coherence
  - Baseline: msp_uncertainty, predictive_entropy, mutual_info
- **Stops until evaluation is configured**

#### Step 5: Review & Launch
- Name the experiment
- Review all configuration sections
- Launch experiment or start over

### 🎨 Visual Design

```
┌─────────────────────────────────────┐
│  Sidebar: Progress Tracker          │
│  ✅ Dataset Selection                │
│  ✅ Training Setup                   │
│  ⬜ Uncertainty Config               │
│  ⬜ Evaluation Setup                 │
│                                      │
│  [🔄 Start Over]                     │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Main Area                           │
│                                      │
│  ✅ Step 1: Dataset - CIFAR10       │
│     [Edit]                           │
│                                      │
│  ✅ Step 2: Training - dinov2-small │
│     [Edit]                           │
│                                      │
│  ┌─────────────────────────────┐   │
│  │ 🎲 Step 3: Uncertainty      │   │
│  │ Configuration (ACTIVE)      │   │
│  │                             │   │
│  │ [Configuration UI]          │   │
│  │                             │   │
│  │ [✓ Continue to Evaluation]  │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Usage

### Running the App

```bash
# From uqlab-streamlit directory
streamlit run streamlit_app_progressive.py

# Or with custom API URL
API_URL=http://localhost:8000 streamlit run streamlit_app_progressive.py
```

### Environment Variables

- `API_URL`: FastAPI backend URL (default: `http://localhost:8000`)
- `API_TOKEN`: Optional authentication token

### Workflow Example

1. **Start**: App shows Step 1 (Dataset Selection)
2. **Select dataset**: Choose CIFAR-10, noise type
3. **Click Continue**: Step 1 collapses, Step 2 appears
4. **Configure training**: Choose model or checkpoint
5. **Click Continue**: Step 2 collapses, Step 3 appears
6. **Configure uncertainty**: Set epistemic/aleatoric parameters
7. **Click Continue**: Step 3 collapses, Step 4 appears
8. **Configure evaluation**: Set pool size, signals
9. **Click Continue**: Step 4 collapses, Step 5 appears
10. **Review & Launch**: Name experiment, review config, launch

### Editing Previous Steps

At any point, you can:
- Click **"Edit"** on a completed step to modify it
- Click **"🔄 Start Over"** in sidebar to reset everything
- Click **"← Start Over"** in Step 5 to reset

## Comparison with Original App

### Original App (`streamlit_app.py`)
- **Layout**: Tab-based (Single Experiment, Batch Experiments)
- **Visibility**: All configuration visible at once
- **Cognitive load**: High (many options visible simultaneously)
- **Validation**: Form-based (submit at end)
- **Navigation**: Free-form (can configure in any order)

### Progressive App (`streamlit_app_progressive.py`)
- **Layout**: Step-by-step linear flow
- **Visibility**: One step at a time
- **Cognitive load**: Low (focus on current step only)
- **Validation**: Progressive (validate each step before continuing)
- **Navigation**: Guided (must complete steps in order)

## Technical Implementation

### Key Patterns

#### 1. Session State Management
```python
st.session_state.workflow = {
    'step1_complete': False,
    'step2_complete': False,
    'step3_complete': False,
    'step4_complete': False,
    'dataset_config': {},
    'training_config': {},
    'uncertainty_config': {},
    'evaluation_config': {},
}
```

#### 2. Progressive Disclosure with `st.stop()`
```python
if not workflow['step1_complete']:
    # Show Step 1 UI
    if st.button("Continue"):
        workflow['step1_complete'] = True
        st.rerun()
    st.stop()  # Halt execution here

# Step 2 only appears after Step 1 is complete
if not workflow['step2_complete']:
    # Show Step 2 UI
    st.stop()
```

#### 3. Collapsed Summaries
```python
if workflow['step1_complete']:
    st.markdown('<div class="step-complete">', unsafe_allow_html=True)
    st.markdown("✅ Step 1: Dataset - CIFAR10")
    if st.button("Edit"):
        workflow['step1_complete'] = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
```

#### 4. No-Default Selectbox
```python
def selectbox_without_default(label, options, help_text=None):
    """Forces user to make explicit selection"""
    options_with_empty = [''] + list(options)
    format_func = lambda x: '⬇️ Select one option' if x == '' else x
    return st.selectbox(label, options_with_empty, format_func=format_func)
```

### Integration Points

#### FastAPI Backend
- `GET /api/v1/datasets/{dataset_name}/stats` - Fetch dataset statistics
- `GET /api/v1/experiments` - List experiments (for checkpoint selection)
- `POST /api/v1/experiments/no-auth` - Create experiment

#### UI Components
- `build_base_experiment_config()` - Build experiment configuration dict
- Reuses existing `ui_components` module for config building

## Benefits

### For Users
- ✅ **Reduced cognitive load**: Focus on one decision at a time
- ✅ **Clear progress**: Always know where you are in the workflow
- ✅ **Fewer errors**: Validation at each step prevents invalid configs
- ✅ **Easy editing**: Modify any previous step without losing progress
- ✅ **Guided experience**: Natural flow from dataset → training → uncertainty → evaluation

### For Developers
- ✅ **Maintainable**: Clear separation of steps
- ✅ **Testable**: Each step can be tested independently
- ✅ **Extensible**: Easy to add new steps or modify existing ones
- ✅ **Reusable**: Pattern can be applied to other workflows

## Future Enhancements

### Planned Features
1. **Step validation indicators**: Show checkmarks for valid configurations
2. **Estimated runtime**: Display expected experiment duration
3. **Configuration templates**: Save/load common configurations
4. **Batch mode**: Create multiple experiments with parameter sweeps
5. **Real-time preview**: Show dataset/model visualizations
6. **Experiment comparison**: Compare with previous experiments

### Integration Opportunities
1. **Experiment tracker**: Link to `experiment_tracker` visualization
2. **Cloud mode**: Integrate watsonx.ai cloud inference
3. **Advanced signals**: Add custom uncertainty signal definitions
4. **Model zoo**: Browse and select from pre-trained models

## Troubleshooting

### Common Issues

#### Backend Connection Error
```
Failed to fetch dataset stats: Connection refused
```
**Solution**: Ensure FastAPI backend is running on `http://localhost:8000`

#### Import Error
```
ModuleNotFoundError: No module named 'ui_components'
```
**Solution**: Run from `uqlab-streamlit` directory or ensure `src/` is in PYTHONPATH

#### Session State Reset
**Issue**: Configuration lost after page refresh
**Solution**: This is expected Streamlit behavior. Use "Review & Launch" to save config.

## Migration Guide

### From Original App

If you're familiar with `streamlit_app.py`:

| Original Feature | Progressive Equivalent |
|-----------------|------------------------|
| Dataset selection dropdown | Step 1: Dataset Selection |
| Epistemic/Aleatoric columns | Step 3: Uncertainty Config (split into columns) |
| Model & Training section | Step 2: Training Setup |
| Evaluation config | Step 4: Evaluation Setup |
| Form submit button | Step 5: Review & Launch |
| Batch experiments tab | Not yet implemented (future) |

### Key Differences
1. **No tabs**: Linear flow instead of tab-based navigation
2. **No form**: Each step validates independently
3. **No defaults**: Must explicitly select all options
4. **Progressive**: Can't skip ahead to later steps

## Related Documentation

- `STREAMLIT_PROGRESSIVE_UX_SPEC.md` - Detailed UX specification
- `STREAMLIT_REDESIGN_PLAN.md` - Master-detail layout architecture
- `EXPERIMENT_TRACKER_INTEGRATION_PLAN.md` - Visualization integration

## Credits

Inspired by:
- **MLflow UI**: Progressive disclosure pattern with `st.stop()`
- **Material Design**: Progressive disclosure principles
- **Nielsen Norman Group**: UX research on cognitive load reduction

---

**Status**: ✅ Production-ready
**Version**: 1.0.0
**Last Updated**: 2026-06-03