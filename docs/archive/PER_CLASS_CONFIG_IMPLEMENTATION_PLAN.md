# Per-Class Configuration Implementation Plan

**Goal**: Replace global class assignment with explicit per-class configuration in Steps 3 & 4

**User Requirements**:
- Label-based (per-class) assignment in Step 3 & 4
- Choose epistemic (under-train) and aleatoric (label noise) parameters for each class
- Enable sweep per class with quick/full presets
- Support sweeping individual classes or multiple classes together

---

## Phase 1: Data Model (Backend Config)

### 1.1 Create PerClassConfig Dataclass

**File**: `src/uqlab/shared/config/classification.py`

```python
@dataclass
class PerClassConfig:
    """Configuration for a single class."""
    class_id: int
    class_name: str  # e.g., "airplane", "cat"
    train_samples: int = 300
    label_noise_pct: float = 0.0
    sweep_epistemic: bool = False  # Sweep train_samples?
    sweep_aleatoric: bool = False  # Sweep label_noise_pct?
    
    def __post_init__(self):
        if self.sweep_epistemic and self.sweep_aleatoric:
            raise ValueError(f"Class {self.class_id} cannot sweep both epistemic and aleatoric")
```

### 1.2 Update DataConfig

**File**: `src/uqlab/shared/config/classification.py`

```python
@dataclass
class DataConfig:
    dataset_name: str = "cifar10"
    noise_type: str = "clean_label"
    eval_per_group: int = 100
    
    # NEW: Per-class configuration (replaces global settings)
    per_class_config: Optional[Dict[int, PerClassConfig]] = None
    
    # LEGACY: Keep for backward compatibility, convert to per_class_config internally
    under_supported_classes: Optional[List[int]] = None
    under_train_per_class: int = 50
    regular_train_per_class: int = 300
    aleatoric_noise_percentage: float = 0.0
    
    def to_per_class_config(self, num_classes: int = 10) -> Dict[int, PerClassConfig]:
        """Convert legacy config to per-class format."""
        if self.per_class_config:
            return self.per_class_config
            
        # Convert legacy global settings to per-class
        per_class = {}
        under_classes = set(self.under_supported_classes or [])
        
        for class_id in range(num_classes):
            is_under = class_id in under_classes
            per_class[class_id] = PerClassConfig(
                class_id=class_id,
                class_name=f"class_{class_id}",  # Will be replaced with actual names
                train_samples=self.under_train_per_class if is_under else self.regular_train_per_class,
                label_noise_pct=0.0 if is_under else self.aleatoric_noise_percentage,
                sweep_epistemic=False,
                sweep_aleatoric=False,
            )
        return per_class
```

---

## Phase 2: UI Components (Step 3)

### 2.1 Create Per-Class Configuration Table

**File**: `src/uqlab/ui_components/workflow/step3_per_class_table.py` (NEW)

```python
import streamlit as st
from typing import Dict, List, Tuple

CIFAR10_CLASS_NAMES = [
    "airplane", "automobile", "bird", "cat", "deer",
    "dog", "frog", "horse", "ship", "truck"
]

def render_per_class_table(
    workflow: dict,
    class_names: List[str] = CIFAR10_CLASS_NAMES
) -> Tuple[Dict[int, dict], bool]:
    """
    Render per-class configuration table.
    
    Returns:
        (per_class_config, is_complete)
    """
    st.markdown("### 📋 Per-Class Configuration")
    st.info("Configure training samples and label noise for each class. Enable sweep to vary that parameter.")
    
    # Initialize session state
    if 'per_class_config' not in st.session_state:
        st.session_state.per_class_config = {
            i: {
                'train_samples': 300,
                'label_noise_pct': 0.0,
                'sweep_epistemic': False,
                'sweep_aleatoric': False,
            }
            for i in range(len(class_names))
        }
    
    # Quick presets
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎯 Paper Default", help="2 sparse (50 samples), 8 regular (300 samples), 0% noise"):
            _apply_paper_default(class_names)
    with col2:
        if st.button("⚖️ Balanced", help="All classes: 300 samples, 0% noise"):
            _apply_balanced(class_names)
    with col3:
        if st.button("🔄 Reset", help="Reset to defaults"):
            _reset_config(class_names)
    
    st.markdown("---")
    
    # Table header
    cols = st.columns([1, 2, 2, 2, 2, 2])
    cols[0].markdown("**ID**")
    cols[1].markdown("**Class**")
    cols[2].markdown("**Train Samples**")
    cols[3].markdown("**Label Noise %**")
    cols[4].markdown("**Sweep Epistemic**")
    cols[5].markdown("**Sweep Aleatoric**")
    
    # Table rows
    per_class_config = {}
    has_sweep = False
    
    for class_id, class_name in enumerate(class_names):
        cols = st.columns([1, 2, 2, 2, 2, 2])
        
        # Class ID and name
        cols[0].markdown(f"`{class_id}`")
        cols[1].markdown(f"**{class_name}**")
        
        # Train samples
        train_samples = cols[2].number_input(
            "samples",
            min_value=10,
            max_value=500,
            value=st.session_state.per_class_config[class_id]['train_samples'],
            step=10,
            key=f"train_{class_id}",
            label_visibility="collapsed"
        )
        
        # Label noise %
        label_noise = cols[3].number_input(
            "noise",
            min_value=0.0,
            max_value=100.0,
            value=st.session_state.per_class_config[class_id]['label_noise_pct'],
            step=5.0,
            key=f"noise_{class_id}",
            label_visibility="collapsed"
        )
        
        # Sweep checkboxes
        sweep_epist = cols[4].checkbox(
            "epist",
            value=st.session_state.per_class_config[class_id]['sweep_epistemic'],
            key=f"sweep_epist_{class_id}",
            label_visibility="collapsed"
        )
        
        sweep_aleat = cols[5].checkbox(
            "aleat",
            value=st.session_state.per_class_config[class_id]['sweep_aleatoric'],
            key=f"sweep_aleat_{class_id}",
            label_visibility="collapsed",
            disabled=sweep_epist  # Can't sweep both
        )
        
        # Validate: can't sweep both
        if sweep_epist and sweep_aleat:
            st.error(f"Class {class_id} ({class_name}): Cannot sweep both epistemic and aleatoric")
            sweep_aleat = False
        
        # Update session state
        st.session_state.per_class_config[class_id] = {
            'train_samples': train_samples,
            'label_noise_pct': label_noise,
            'sweep_epistemic': sweep_epist,
            'sweep_aleatoric': sweep_aleat,
        }
        
        per_class_config[class_id] = {
            'class_name': class_name,
            **st.session_state.per_class_config[class_id]
        }
        
        if sweep_epist or sweep_aleat:
            has_sweep = True
    
    # Summary
    st.markdown("---")
    _render_summary(per_class_config, class_names)
    
    is_complete = True  # Always complete if table is filled
    return per_class_config, is_complete, has_sweep


def _apply_paper_default(class_names):
    """Apply paper default: 2 sparse, 8 regular."""
    import random
    sparse_classes = random.sample(range(len(class_names)), 2)
    for i in range(len(class_names)):
        st.session_state.per_class_config[i] = {
            'train_samples': 50 if i in sparse_classes else 300,
            'label_noise_pct': 0.0,
            'sweep_epistemic': False,
            'sweep_aleatoric': False,
        }


def _apply_balanced(class_names):
    """Apply balanced: all 300 samples, 0% noise."""
    for i in range(len(class_names)):
        st.session_state.per_class_config[i] = {
            'train_samples': 300,
            'label_noise_pct': 0.0,
            'sweep_epistemic': False,
            'sweep_aleatoric': False,
        }


def _reset_config(class_names):
    """Reset to defaults."""
    _apply_balanced(class_names)


def _render_summary(per_class_config, class_names):
    """Render configuration summary."""
    total_train = sum(cfg['train_samples'] for cfg in per_class_config.values())
    avg_noise = sum(cfg['label_noise_pct'] for cfg in per_class_config.values()) / len(class_names)
    
    sweep_epist_classes = [i for i, cfg in per_class_config.items() if cfg['sweep_epistemic']]
    sweep_aleat_classes = [i for i, cfg in per_class_config.items() if cfg['sweep_aleatoric']]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Training Samples", f"{total_train:,}")
    col2.metric("Avg Label Noise", f"{avg_noise:.1f}%")
    col3.metric("Classes with Sweep", len(sweep_epist_classes) + len(sweep_aleat_classes))
    
    if sweep_epist_classes:
        st.info(f"🔄 **Epistemic sweep** enabled for classes: {', '.join(str(i) for i in sweep_epist_classes)}")
    if sweep_aleat_classes:
        st.info(f"🔄 **Aleatoric sweep** enabled for classes: {', '.join(str(i) for i in sweep_aleat_classes)}")
```

### 2.2 Update Step 3 Main Component

**File**: `src/uqlab/ui_components/workflow/step3_uncertainty.py`

Replace current epistemic/aleatoric sections with:

```python
from uqlab.ui_components.workflow.step3_per_class_table import render_per_class_table

def render_step3_active(workflow: dict) -> None:
    """Active Step 3 form — per-class configuration."""
    st.markdown("### Step 3: Per-Class Uncertainty Configuration")
    
    per_class_config, is_complete, has_sweep = render_per_class_table(workflow)
    
    if not has_sweep:
        st.warning("⚠️ No sweep enabled. Enable sweep for at least one class to generate experiments.")
    
    # Continue button
    if st.button("Continue to Step 4", type="primary", disabled=not is_complete):
        workflow["step3_complete"] = True
        workflow["uncertainty_config"] = {
            "per_class_config": per_class_config,
            "has_sweep": has_sweep,
        }
        st.success("✅ Step 3 complete")
        st.rerun()
```

---

## Phase 3: Sweep Configuration (Step 4)

### 3.1 Create Sweep Preset Selector

**File**: `src/uqlab/ui_components/workflow/step4_sweep_presets.py` (NEW)

```python
import streamlit as st
from typing import List, Dict

EPISTEMIC_PRESETS = {
    "quick": [25, 50, 100, 150, 200],
    "full": [25, 52, 80, 108, 135, 162, 190, 218, 245, 272, 300],
    "paper": [50, 100, 150, 200, 250, 300],
}

ALEATORIC_PRESETS = {
    "quick": [0, 20, 40, 60, 80, 100],
    "full": [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
    "paper": [0, 25, 50, 75, 100],
}

def render_sweep_presets(per_class_config: Dict[int, dict]) -> Dict[str, any]:
    """
    Render sweep preset selection for classes with sweep enabled.
    
    Returns sweep configuration dict.
    """
    st.markdown("### 🔄 Sweep Configuration")
    
    sweep_epist_classes = [i for i, cfg in per_class_config.items() if cfg['sweep_epistemic']]
    sweep_aleat_classes = [i for i, cfg in per_class_config.items() if cfg['sweep_aleatoric']]
    
    sweep_config = {}
    
    # Epistemic sweeps
    if sweep_epist_classes:
        st.markdown("#### Epistemic Sweep (Training Samples)")
        
        for class_id in sweep_epist_classes:
            class_name = per_class_config[class_id]['class_name']
            
            with st.expander(f"Class {class_id}: {class_name}", expanded=True):
                preset = st.selectbox(
                    "Preset",
                    options=["quick", "full", "paper", "custom"],
                    key=f"epist_preset_{class_id}"
                )
                
                if preset == "custom":
                    values_str = st.text_input(
                        "Values (comma-separated)",
                        value="25,50,100,150,200",
                        key=f"epist_custom_{class_id}"
                    )
                    values = [int(v.strip()) for v in values_str.split(",")]
                else:
                    values = EPISTEMIC_PRESETS[preset]
                    st.info(f"Values: {values}")
                
                sweep_config[f"epistemic_{class_id}"] = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'type': 'epistemic',
                    'values': values,
                }
    
    # Aleatoric sweeps
    if sweep_aleat_classes:
        st.markdown("#### Aleatoric Sweep (Label Noise %)")
        
        for class_id in sweep_aleat_classes:
            class_name = per_class_config[class_id]['class_name']
            
            with st.expander(f"Class {class_id}: {class_name}", expanded=True):
                preset = st.selectbox(
                    "Preset",
                    options=["quick", "full", "paper", "custom"],
                    key=f"aleat_preset_{class_id}"
                )
                
                if preset == "custom":
                    values_str = st.text_input(
                        "Values (comma-separated)",
                        value="0,20,40,60,80,100",
                        key=f"aleat_custom_{class_id}"
                    )
                    values = [float(v.strip()) for v in values_str.split(",")]
                else:
                    values = ALEATORIC_PRESETS[preset]
                    st.info(f"Values: {values}")
                
                sweep_config[f"aleatoric_{class_id}"] = {
                    'class_id': class_id,
                    'class_name': class_name,
                    'type': 'aleatoric',
                    'values': values,
                }
    
    return sweep_config
```

---

## Phase 4: Config Conversion & Sweep Generation

### 4.1 Convert Per-Class Config to Experiments

**File**: `src/uqlab_orchestrator/per_class_sweep.py` (NEW)

```python
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class PerClassExperimentConfig:
    """Single experiment configuration from per-class sweep."""
    name: str
    per_class_settings: Dict[int, dict]  # class_id -> {train_samples, label_noise_pct}
    swept_class: int
    swept_param: str  # "train_samples" or "label_noise_pct"
    swept_value: float

def generate_per_class_experiments(
    base_per_class_config: Dict[int, dict],
    sweep_config: Dict[str, dict],
    timestamp: str
) -> List[PerClassExperimentConfig]:
    """
    Generate experiment configs from per-class sweep configuration.
    
    Args:
        base_per_class_config: Base config for all classes
        sweep_config: Sweep definitions from step 4
        timestamp: Timestamp for experiment naming
    
    Returns:
        List of experiment configurations
    """
    experiments = []
    
    for sweep_key, sweep_def in sweep_config.items():
        class_id = sweep_def['class_id']
        sweep_type = sweep_def['type']
        values = sweep_def['values']
        
        for value in values:
            # Copy base config
            per_class_settings = {
                cid: {
                    'train_samples': cfg['train_samples'],
                    'label_noise_pct': cfg['label_noise_pct'],
                }
                for cid, cfg in base_per_class_config.items()
            }
            
            # Apply swept value
            if sweep_type == 'epistemic':
                per_class_settings[class_id]['train_samples'] = int(value)
                param_name = "train_samples"
            else:  # aleatoric
                per_class_settings[class_id]['label_noise_pct'] = float(value)
                param_name = "label_noise_pct"
            
            # Generate name
            class_name = base_per_class_config[class_id]['class_name']
            name = f"{sweep_type}_{timestamp}_class{class_id}_{class_name}_{param_name}_{value}"
            
            experiments.append(PerClassExperimentConfig(
                name=name,
                per_class_settings=per_class_settings,
                swept_class=class_id,
                swept_param=param_name,
                swept_value=value,
            ))
    
    return experiments
```

---

## Phase 5: Backend Integration

### 5.1 Update Data Loader

**File**: `src/uqlab/evaluation/pipeline/data_setup.py`

Add function to convert per-class config to legacy format:

```python
def per_class_to_legacy_format(
    per_class_config: Dict[int, PerClassConfig]
) -> tuple[List[int], int, int, float]:
    """
    Convert per-class config to legacy format for data loader.
    
    Returns:
        (under_supported_classes, under_train_per_class, regular_train_per_class, aleatoric_noise_percentage)
    """
    # Find classes with < 300 samples (sparse/epistemic)
    under_classes = [
        cid for cid, cfg in per_class_config.items()
        if cfg.train_samples < 300
    ]
    
    # Get representative values (use most common)
    under_samples = [cfg.train_samples for cfg in per_class_config.values() if cfg.train_samples < 300]
    regular_samples = [cfg.train_samples for cfg in per_class_config.values() if cfg.train_samples >= 300]
    
    under_train = min(under_samples) if under_samples else 50
    regular_train = max(regular_samples) if regular_samples else 300
    
    # Average noise for regular classes
    regular_noise = [
        cfg.label_noise_pct for cid, cfg in per_class_config.items()
        if cid not in under_classes
    ]
    avg_noise = sum(regular_noise) / len(regular_noise) if regular_noise else 0.0
    
    return under_classes, under_train, regular_train, avg_noise
```

---

## Implementation Order

1. **Phase 1**: Data model (30 min)
   - Add PerClassConfig dataclass
   - Update DataConfig with per_class_config field
   - Add conversion methods

2. **Phase 2**: Step 3 UI (90 min)
   - Create per-class table component
   - Add presets (paper default, balanced, reset)
   - Update step3_uncertainty.py

3. **Phase 3**: Step 4 UI (60 min)
   - Create sweep preset selector
   - Support quick/full/paper/custom presets per class

4. **Phase 4**: Sweep generation (45 min)
   - Create per_class_sweep.py
   - Generate experiment configs from per-class + sweep settings

5. **Phase 5**: Backend integration (45 min)
   - Add per_class_to_legacy_format converter
   - Update run_spec.py to handle per-class config
   - Test end-to-end flow

**Total Estimated Time**: 4-5 hours

---

## Testing Plan

1. **Unit Tests**:
   - PerClassConfig validation
   - Conversion functions (per-class ↔ legacy)
   - Sweep generation logic

2. **Integration Tests**:
   - UI flow: Step 3 → Step 4 → Launch
   - Config persistence in session state
   - Experiment generation with various sweep combinations

3. **Manual Testing**:
   - Paper default preset
   - Custom per-class configurations
   - Multiple classes with sweeps
   - Single class sweep vs. multiple class sweeps

---

## Backward Compatibility

- Keep legacy fields in DataConfig
- Auto-convert legacy → per-class on load
- Data loader accepts both formats
- Existing experiments continue to work

---

## Future Enhancements

- Import/export per-class config as CSV
- Visualize per-class distribution before launch
- Class grouping (e.g., "animals" vs. "vehicles")
- Per-class evaluation pool sizes