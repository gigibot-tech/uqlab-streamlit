# Streamlit Progressive Disclosure UX Specification

## Overview

A redesigned Streamlit interface using **progressive disclosure** UX pattern inspired by MLflow/experiment tracker workflows. Each configuration step appears only after the previous step is completed, creating a guided, linear flow that reduces cognitive load and prevents configuration errors.

## Design Philosophy

### Core Principles
1. **Progressive Disclosure**: Show only what's needed at each step
2. **Visual Feedback**: Clear indication of completed vs pending steps
3. **Collapsible Sections**: Completed steps collapse to save space
4. **Master-Detail Pattern**: Left sidebar shows progress, main area shows current step
5. **Validation Gates**: Can't proceed until current step is valid

### Inspiration Sources
- **MLflow UI**: Run selection → metrics visualization flow
- **Experiment Tracker**: Dataset selection → parallel coordinates exploration
- **Wizard Pattern**: Step-by-step configuration with progress tracking

---

## User Flow Architecture

### Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    SIDEBAR (Always Visible)                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Progress Tracker                                       │  │
│  │ ✅ 1. Dataset Selection                               │  │
│  │ ⏳ 2. Training Configuration                          │  │
│  │ ⬜ 3. Uncertainty Configuration                       │  │
│  │ ⬜ 4. Evaluation Setup                                │  │
│  │ ⬜ 5. Review & Launch                                 │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    MAIN AREA (Current Step)                  │
│                                                              │
│  [Current step content with "Continue" button]              │
│                                                              │
│  [Completed steps shown as collapsed cards above]           │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Step Specifications

### Step 1: Dataset Selection 📊

**Purpose**: Select dataset and view statistics

**UI Elements**:
```python
# Expanded view (active)
┌─────────────────────────────────────────────────────────┐
│ 📊 Step 1: Dataset Selection                            │
│                                                          │
│ Select Dataset: [CIFAR-10 ▼]                           │
│ Noise Type:     [worse_label ▼]                        │
│                                                          │
│ Dataset Statistics:                                      │
│ • Total samples: 50,000                                 │
│ • Classes: 10                                           │
│ • Noise rate: 40.2% (CIFAR-10N)                        │
│                                                          │
│ [✓ Continue to Training Configuration]                  │
└─────────────────────────────────────────────────────────┘

# Collapsed view (completed)
┌─────────────────────────────────────────────────────────┐
│ ✅ Dataset: CIFAR-10 (worse_label) [Edit]              │
└─────────────────────────────────────────────────────────┘
```

**Session State**:
```python
st.session_state.step1_complete = True
st.session_state.dataset_name = "cifar10"  # Base dataset
st.session_state.noise_type = "worse_label"  # CIFAR-10N noise variant
st.session_state.dataset_stats = {...}
```

**Validation**:
- Dataset must be selected
- Stats must load successfully

---

### Step 2: Training Configuration 🧠

**Purpose**: Choose between training new model or using checkpoint

**UI Elements**:
```python
┌─────────────────────────────────────────────────────────┐
│ 🧠 Step 2: Training Configuration                       │
│                                                          │
│ ○ Train New Model                                       │
│   ├─ Model Architecture: [DINOv2-small ▼]              │
│   ├─ Hidden Dimension: [256]                            │
│   ├─ Dropout: [0.2]                                     │
│   ├─ Epochs: [12]                                       │
│   ├─ Learning Rate: [0.001]                             │
│   └─ Batch Size: [256]                                  │
│                                                          │
│ ● Use Existing Checkpoint                               │
│   └─ Select Checkpoint: [exp_20240603_142301 ▼]        │
│                                                          │
│ [✓ Continue to Uncertainty Configuration]               │
└─────────────────────────────────────────────────────────┘
```

**Session State**:
```python
st.session_state.step2_complete = True
st.session_state.use_checkpoint = True/False
st.session_state.model_config = {...}  # if training
st.session_state.checkpoint_id = "..."  # if using checkpoint
```

**Validation**:
- If training: all model params must be valid
- If checkpoint: checkpoint must be selected and exist

---

### Step 3: Uncertainty Configuration 🎲

**Purpose**: Configure epistemic and aleatoric uncertainty

**UI Elements**:
```python
┌─────────────────────────────────────────────────────────┐
│ 🎲 Step 3: Uncertainty Configuration                    │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Epistemic Uncertainty (Dataset Size)                │ │
│ │                                                      │ │
│ │ ○ No Sweep (Use full dataset)                       │ │
│ │ ● Dataset Size Sweep                                │ │
│ │   ├─ Under-supported classes: [random:2 ▼]         │ │
│ │   ├─ Under-supported samples: [50]                  │ │
│ │   └─ Regular class samples: [300]                   │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Aleatoric Uncertainty (Label Noise)                 │ │
│ │                                                      │ │
│ │ ● Use dataset noise (CIFAR-10N: 40.2%)             │ │
│ │ ○ Custom noise rate: [__]%                          │ │
│ │ ○ No additional noise                               │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Dataset Preview:                                         │
│ • Under-supported: 2 classes × 50 = 100 samples        │
│ • Regular: 8 classes × 300 = 2,400 samples             │
│ • Total training: 2,500 samples                         │
│                                                          │
│ [✓ Continue to Evaluation Setup]                        │
└─────────────────────────────────────────────────────────┘
```

**Session State**:
```python
st.session_state.step3_complete = True
st.session_state.epistemic_config = {
    "sweep_enabled": True/False,
    "under_supported": "random:2",
    "under_train_per_class": 50,
    "regular_train_per_class": 300
}
st.session_state.aleatoric_config = {
    "noise_source": "dataset" | "custom" | "none",  # "dataset" uses CIFAR-10N
    "custom_noise_rate": 0.0
}
```

**Validation**:
- At least one uncertainty type must be configured
- Sample counts must be positive integers
- Custom noise rate must be 0-100%

---

### Step 4: Evaluation Setup 📊

**Purpose**: Configure evaluation strategy based on dataset

**UI Elements**:
```python
┌─────────────────────────────────────────────────────────┐
│ 📊 Step 4: Evaluation Setup                             │
│                                                          │
│ Evaluation Pool (based on dataset configuration):       │
│ • Total available: 47,500 samples                       │
│ • Recommended per group: 100-500 samples                │
│                                                          │
│ Samples per group: [100]                                │
│                                                          │
│ Evaluation Groups:                                       │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Group              | Samples | Description          │ │
│ ├─────────────────────────────────────────────────────┤ │
│ │ Under-supported    | 100     | Low data classes    │ │
│ │ Regular (clean)    | 100     | Normal, no noise    │ │
│ │ Regular (noisy)    | 100     | Normal, with noise  │ │
│ │ Total              | 300     |                      │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ MC Dropout Passes: [20]                                 │
│                                                          │
│ Uncertainty Signals:                                     │
│ ☑ Epistemic: inverse_mass, dominance, inverse_logit    │
│ ☑ Aleatoric: inverse_coherence                         │
│ ☑ Baseline: msp_uncertainty, predictive_entropy        │
│                                                          │
│ [✓ Continue to Review & Launch]                         │
└─────────────────────────────────────────────────────────┘
```

**Session State**:
```python
st.session_state.step4_complete = True
st.session_state.eval_config = {
    "eval_per_group": 100,
    "mc_passes": 20,
    "selected_signals": [...]
}
```

**Validation**:
- eval_per_group must be positive
- mc_passes must be >= 1
- At least one signal must be selected

---

### Step 5: Review & Launch 🚀

**Purpose**: Review all configuration and launch experiment

**UI Elements**:
```python
┌─────────────────────────────────────────────────────────┐
│ 🚀 Step 5: Review & Launch                              │
│                                                          │
│ Experiment Name: [exp_20240603_182045]                  │
│                                                          │
│ Configuration Summary:                                   │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ 📊 Dataset                                           │ │
│ │ • CIFAR-10 with CIFAR-10N noise (worse_label)       │ │
│ │ • 50,000 samples, 10 classes                        │ │
│ │                                                      │ │
│ │ 🧠 Training                                          │ │
│ │ • Using checkpoint: exp_20240603_142301             │ │
│ │                                                      │ │
│ │ 🎲 Uncertainty                                       │ │
│ │ • Epistemic: Dataset size sweep (2 under-supported) │ │
│ │ • Aleatoric: Dataset noise (CIFAR-10N: 40.2%)      │ │
│ │                                                      │ │
│ │ 📊 Evaluation                                        │ │
│ │ • 100 samples per group (3 groups = 300 total)     │ │
│ │ • 20 MC dropout passes                              │ │
│ │ • 6 uncertainty signals                             │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                          │
│ Estimated Runtime: ~15 minutes                           │
│                                                          │
│ [🚀 Launch Experiment]  [← Back to Edit]               │
└─────────────────────────────────────────────────────────┘
```

**Actions**:
- Launch experiment via API
- Show progress bar
- Redirect to results view on completion

---

## Implementation Architecture

### File Structure

```
walaris-cen/
├── streamlit_app_progressive.py          # New main app
├── ui_components/
│   └── progressive/
│       ├── __init__.py
│       ├── step1_dataset.py              # Dataset selection
│       ├── step2_training.py             # Training config
│       ├── step3_uncertainty.py          # Uncertainty config
│       ├── step4_evaluation.py           # Evaluation setup
│       ├── step5_review.py               # Review & launch
│       ├── progress_tracker.py           # Sidebar progress
│       ├── collapsed_card.py             # Completed step cards
│       └── validation.py                 # Step validation logic
```

### Session State Management

```python
# Initialize session state
if 'workflow_state' not in st.session_state:
    st.session_state.workflow_state = {
        'current_step': 1,
        'completed_steps': set(),
        'step1_data': {},
        'step2_data': {},
        'step3_data': {},
        'step4_data': {},
        'step5_data': {},
    }

# Step completion tracking
def mark_step_complete(step_num: int):
    st.session_state.workflow_state['completed_steps'].add(step_num)
    st.session_state.workflow_state['current_step'] = step_num + 1

# Step validation
def can_proceed_to_step(step_num: int) -> bool:
    return (step_num - 1) in st.session_state.workflow_state['completed_steps']
```

### Component API

Each step component follows this interface:

```python
def render_step_N(
    data: dict,
    on_complete: Callable[[dict], None],
    on_edit: Callable[[], None]
) -> None:
    """
    Render step N of the workflow.
    
    Args:
        data: Pre-filled data from previous session (if editing)
        on_complete: Callback when step is completed with valid data
        on_edit: Callback when user wants to edit this step
    """
    # Render UI
    # Validate inputs
    # Call on_complete(validated_data) when ready
```

---

## Visual Design System

### Color Palette

```python
COLORS = {
    'primary': '#4CAF50',      # Green for completed/active
    'secondary': '#2196F3',    # Blue for info
    'warning': '#FF9800',      # Orange for warnings
    'error': '#F44336',        # Red for errors
    'muted': '#9E9E9E',        # Gray for disabled/pending
    'background': '#FAFAFA',   # Light gray background
}
```

### Step States

```python
# Pending (not yet reached)
⬜ Step Name (grayed out, not clickable)

# Active (current step)
⏳ Step Name (highlighted, expanded)

# Completed (can be edited)
✅ Step Name (collapsed, clickable to expand)

# Error (validation failed)
❌ Step Name (red, must fix before proceeding)
```

### Animations

```css
/* Smooth step transitions */
.step-container {
    transition: all 0.3s ease-in-out;
}

/* Collapse animation */
.collapsed {
    max-height: 60px;
    overflow: hidden;
}

.expanded {
    max-height: 2000px;
}

/* Progress indicator pulse */
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.active-step {
    animation: pulse 2s infinite;
}
```

---

## Integration with Existing Backend

### API Endpoints Used

```python
# Step 1: Dataset
GET /api/v1/datasets/{dataset_name}/stats

# Step 2: Training (checkpoint mode)
GET /api/v1/experiments  # List available checkpoints

# Step 5: Launch
POST /api/v1/experiments/no-auth
{
    "name": "exp_20240603_182045",
    "config": {
        # Merged config from all steps
    }
}
```

### Config Builder

```python
def build_experiment_config(workflow_state: dict) -> dict:
    """
    Build complete experiment config from workflow state.
    
    Merges data from all 5 steps into format expected by backend API.
    """
    return {
        "dataset": workflow_state['step1_data'],
        "training": workflow_state['step2_data'],
        "epistemic": workflow_state['step3_data']['epistemic_config'],
        "aleatoric": workflow_state['step3_data']['aleatoric_config'],
        "evaluation": workflow_state['step4_data'],
    }
```

---

## Migration Strategy

### Phase 1: Parallel Development (Week 1)
- Create new `streamlit_app_progressive.py`
- Implement Step 1 (Dataset Selection)
- Test with existing backend

### Phase 2: Core Steps (Week 2)
- Implement Steps 2-4
- Add progress tracker sidebar
- Implement collapsed card UI

### Phase 3: Polish & Integration (Week 3)
- Implement Step 5 (Review & Launch)
- Add animations and transitions
- Connect to results view

### Phase 4: User Testing (Week 4)
- A/B test with current interface
- Gather feedback
- Iterate on UX

### Phase 5: Rollout (Week 5)
- Make progressive UI default
- Keep old UI as "Classic Mode" option
- Update documentation

---

## Success Metrics

### User Experience
- **Time to first experiment**: < 3 minutes (vs 5+ minutes currently)
- **Configuration errors**: < 5% (vs 15% currently)
- **User satisfaction**: > 4.5/5 stars

### Technical
- **Page load time**: < 2 seconds
- **Step transition**: < 300ms
- **Memory usage**: < 500MB

### Business
- **Experiment completion rate**: > 90%
- **Return user rate**: > 70%
- **Support tickets**: -50%

---

## Future Enhancements

### Phase 2 Features
1. **Templates**: Save/load configuration templates
2. **Comparison Mode**: Compare multiple configurations side-by-side
3. **Guided Tours**: Interactive tutorials for new users
4. **Keyboard Shortcuts**: Power user navigation (Ctrl+Enter to continue, etc.)

### Phase 3 Features
1. **Real-time Validation**: Show errors as user types
2. **Smart Defaults**: ML-powered config recommendations
3. **Collaborative Mode**: Share configurations with team
4. **Version Control**: Track configuration changes over time

---

## Appendix: Code Examples

### Example: Step 1 Implementation

```python
# ui_components/progressive/step1_dataset.py

import streamlit as st
from typing import Callable, Optional

def render_step1_dataset(
    data: Optional[dict],
    on_complete: Callable[[dict], None],
    fetch_dataset_stats: Callable
) -> None:
    """Render dataset selection step."""
    
    st.markdown("### 📊 Step 1: Dataset Selection")
    
    # Pre-fill from data if editing
    default_dataset = data.get('dataset_name', 'cifar10n') if data else 'cifar10n'
    default_noise = data.get('noise_type', 'worse_label') if data else 'worse_label'
    
    # Dataset selection
    dataset_name = st.selectbox(
        "Select Dataset",
        options=["cifar10n"],
        index=0,
        key="step1_dataset"
    )
    
    noise_type = st.selectbox(
        "Noise Type",
        options=["worse_label", "random_label1", "random_label2"],
        index=["worse_label", "random_label1", "random_label2"].index(default_noise),
        key="step1_noise"
    )
    
    # Fetch and display stats
    with st.spinner("Loading dataset statistics..."):
        stats = fetch_dataset_stats(dataset_name, noise_type)
    
    if stats:
        st.markdown("#### Dataset Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Samples", f"{stats.get('total_samples', 0):,}")
        with col2:
            st.metric("Classes", stats.get('num_classes', 0))
        with col3:
            st.metric("Noise Rate", f"{stats.get('noise_rate', 0):.1%}")
        
        # Continue button
        if st.button("✓ Continue to Training Configuration", type="primary", use_container_width=True):
            validated_data = {
                'dataset_name': dataset_name,
                'noise_type': noise_type,
                'stats': stats
            }
            on_complete(validated_data)
            st.rerun()
    else:
        st.error("Failed to load dataset statistics. Please try again.")
```

### Example: Progress Tracker

```python
# ui_components/progressive/progress_tracker.py

import streamlit as st

STEPS = [
    {"num": 1, "name": "Dataset Selection", "icon": "📊"},
    {"num": 2, "name": "Training Configuration", "icon": "🧠"},
    {"num": 3, "name": "Uncertainty Configuration", "icon": "🎲"},
    {"num": 4, "name": "Evaluation Setup", "icon": "📊"},
    {"num": 5, "name": "Review & Launch", "icon": "🚀"},
]

def render_progress_tracker(current_step: int, completed_steps: set):
    """Render sidebar progress tracker."""
    
    st.markdown("### ⚙️ Configuration Progress")
    
    for step in STEPS:
        step_num = step['num']
        
        if step_num in completed_steps:
            status = "✅"
            style = "color: #4CAF50; font-weight: bold;"
        elif step_num == current_step:
            status = "⏳"
            style = "color: #2196F3; font-weight: bold;"
        else:
            status = "⬜"
            style = "color: #9E9E9E;"
        
        st.markdown(
            f"<div style='{style}'>{status} {step['icon']} {step['name']}</div>",
            unsafe_allow_html=True
        )
```

---

## Conclusion

This progressive disclosure UX design provides:
- **Reduced cognitive load** through step-by-step guidance
- **Fewer errors** through validation gates
- **Better user experience** with clear progress tracking
- **Faster onboarding** for new users
- **Maintained power** for advanced users through edit functionality

The design is inspired by proven patterns from MLflow and experiment tracker while being tailored to the specific needs of uncertainty quantification experiments.