# UX Redesign Plan: Unified Experiment Workflow

## Executive Summary

**Current Problem**: The UI has 4 separate tabs with redundant configuration, making it difficult to iterate from single experiment → 1D sweep → 2D grid. Users must re-enter the same parameters multiple times.

**Proposed Solution**: Unified workflow where users configure once, then progressively enable sweeps with checkboxes. The UI adapts dynamically based on what's being swept.

---

## Current Issues (Detailed Analysis)

### 1. **Redundant Configuration**
- Dataset config repeated in every tab
- Model/training params duplicated across tabs
- Evaluation settings copied 3 times
- User must remember settings when switching tabs

### 2. **Disconnected Workflow**
- Can't easily go from single experiment → sweep
- No way to see which experiments have similar configs
- Results are separate from configuration
- Can't iterate on interesting experiments

### 3. **Confusing Noise Configuration**
- Two noise sources (CIFAR-10N vs random flipping) not clearly explained
- Average CIFAR-10N noise rate not highlighted
- Relationship between noise types and sweeps unclear

### 4. **Poor Information Architecture**
- "Single Experiment" should be "Experiment Dashboard"
- Results shown after form, not integrated
- No model selection from existing checkpoints
- No warnings about duplicate configurations

---

## Proposed UX: Unified Experiment Builder

### Core Concept: **Progressive Disclosure**

Start simple, reveal complexity only when needed. One configuration view that adapts based on sweep selections.

### New Structure

```
┌─────────────────────────────────────────────────────────────┐
│  🔬 Experiment Builder                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 Dataset Configuration (Compact)                          │
│  ├─ CIFAR-10N (10 classes, avg 40% noise)                  │
│  └─ [Show Details ▼]                                        │
│                                                              │
│  🎯 Uncertainty Configuration                                │
│  ├─ Epistemic: [50] samples/class  [☐ Sweep]               │
│  │   └─ If checked: Range [50, 100, 200]                   │
│  └─ Aleatoric: [40%] noise (CIFAR-10N avg) [☐ Sweep]       │
│      └─ If checked: Range [0, 20, 40, 60]                  │
│                                                              │
│  🧠 Model & Training (Collapsible)                           │
│  ├─ [Use existing checkpoint ▼] or [Configure new ▼]       │
│  └─ Shows: Similar configs, warnings                        │
│                                                              │
│  📊 Evaluation (Collapsible)                                 │
│  └─ Smart defaults based on sweep type                      │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Experiment Type: [Auto-detected]                     │   │
│  │ • Single Experiment (no sweeps)                      │   │
│  │ • 1D Epistemic Sweep (3 experiments)                 │   │
│  │ • 1D Aleatoric Sweep (4 experiments)                 │   │
│  │ • 2D Grid (12 experiments) ✅ Full validation        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  [🚀 Create Experiment(s)]                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  📋 Experiment Dashboard (Below)                             │
├─────────────────────────────────────────────────────────────┤
│  [Filter: All | Running | Completed | Failed]               │
│  [Group by: None | Sweep Type | Model | Date]               │
│                                                              │
│  ┌─ Experiment: exp_20260522_161909 ──────────────────┐    │
│  │  Status: ✅ Completed | AUROC: 0.85 | Duration: 5m  │    │
│  │  Config: epistemic=50, aleatoric=40%, model=small   │    │
│  │  [📊 View Results] [🔁 Clone & Sweep] [💾 Export]   │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌─ Sweep Group: grid_sweep_20260522 ──────────────────┐    │
│  │  Type: 2D Grid (12 experiments) | 10 completed      │    │
│  │  [📊 View Heatmap] [📈 Validation Report]           │    │
│  │  └─ Individual experiments collapsible...            │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Design Specifications

### 1. Dataset Configuration (Simplified)

**Compact View (Default):**
```
📊 Dataset: CIFAR-10N
├─ 10 classes (airplane, automobile, ...)
├─ Noise: 40% average (worse_label type)
└─ [Show class distribution ▼]
```

**Expanded View (Optional):**
- Class-wise noise rates
- Sample counts
- Noise type selector (only if needed)

**Rationale**: Most users don't need to see all details. Show summary, expand on demand.

### 2. Uncertainty Configuration (Core Innovation)

**Epistemic Section:**
```
🔬 Epistemic Uncertainty (Model Uncertainty)
├─ Under-supported classes: [2] random classes
├─ Samples per class: [50] ◄─────────────┐
│                                         │
└─ [☐ Sweep this parameter]              │
    └─ If checked:                        │
        Range: [50, 100, 200]             │
        → Creates 3 experiments           │
        → Tests C2 & O1 conditions        │
```

**Aleatoric Section:**
```
🎲 Aleatoric Uncertainty (Data Uncertainty)
├─ Noise source: 
│   ○ CIFAR-10N (40% avg) [Recommended for validation]
│   ○ Random flipping (custom %)
│
├─ Noise level: [40%] ◄──────────────────┐
│                                         │
└─ [☐ Sweep this parameter]              │
    └─ If checked:                        │
        Range: [0, 20, 40, 60]            │
        → Creates 4 experiments           │
        → Tests C1 & O2 conditions        │
```

**Key Improvements:**
- Checkboxes to enable sweeps (not separate tabs!)
- Noise source clearly explained
- CIFAR-10N average highlighted as recommended
- Sweep ranges shown inline
- Validation conditions explained

### 3. Model Configuration (Smart Defaults)

```
🧠 Model & Training Configuration

[Option 1: Use Existing Checkpoint ▼]
├─ Select from completed experiments
├─ Shows: Similar configs (⚠️ 3 experiments with same settings)
└─ Auto-fills all parameters

[Option 2: Configure New Model ▼]
├─ DINOv2: [small ▼] | Hidden: [256] | Dropout: [0.2]
├─ Epochs: [12] | LR: [0.001] | Batch: [256]
└─ ⚠️ Warning: 2 experiments have similar config
    → Suggest: Change epochs to 15 or LR to 0.0005
```

**Key Improvements:**
- Can reuse existing model configs
- Warns about duplicates
- Suggests parameter changes
- Collapsible to reduce clutter

### 4. Dynamic Experiment Type Detection

```
┌─────────────────────────────────────────────────────────┐
│ 🎯 Experiment Type: [Auto-detected]                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Based on your sweep selections:                         │
│                                                          │
│ ✅ 2D Grid Sweep (12 experiments)                       │
│    ├─ Epistemic: 3 values [50, 100, 200]               │
│    ├─ Aleatoric: 4 values [0, 20, 40, 60]              │
│    └─ Validates: C1, C2, O1, O2 ✅                      │
│                                                          │
│ Estimated time: ~60 minutes                             │
│ Estimated cost: 12 experiments × 5min = 1 hour          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 5. Experiment Dashboard (Results Integration)

**Instead of showing results after form, integrate them:**

```
📋 Experiment Dashboard

[Filters]
├─ Status: [All ▼] [Running ▼] [Completed ▼]
├─ Type: [All ▼] [Single ▼] [1D Sweep ▼] [2D Grid ▼]
└─ Date: [Last 7 days ▼]

[Group by: Sweep Type ▼]

┌─ 2D Grid: grid_sweep_20260522 ────────────────────────┐
│  12 experiments | 10 completed, 2 running             │
│  Epistemic: [50, 100, 200] × Aleatoric: [0, 20, 40, 60]│
│                                                         │
│  [📊 View Heatmap] [📈 Validation Report] [🔁 Clone]   │
│                                                         │
│  └─ [Show individual experiments ▼]                    │
│      ├─ exp_e50_a0: ✅ AUROC 0.82                      │
│      ├─ exp_e50_a20: ✅ AUROC 0.79                     │
│      └─ ... (10 more)                                  │
└─────────────────────────────────────────────────────────┘

┌─ Single: exp_20260522_161909 ─────────────────────────┐
│  ✅ Completed | AUROC: 0.85 | Duration: 5m             │
│  Config: epistemic=50, aleatoric=40%, model=small      │
│                                                         │
│  [📊 View Signals] [🔁 Clone & Sweep] [💾 Export]      │
│                                                         │
│  Signals:                                               │
│  ├─ Epistemic (ue): 0.23 ± 0.05                        │
│  ├─ Aleatoric (ua): 0.45 ± 0.08                        │
│  └─ [View all 7 signals ▼]                             │
│                                                         │
│  Actions:                                               │
│  ├─ [🔁 Sweep Epistemic] → Creates 1D sweep            │
│  └─ [🔁 Sweep Aleatoric] → Creates 1D sweep            │
└─────────────────────────────────────────────────────────┘
```

**Key Features:**
- Results integrated with configuration
- "Clone & Sweep" button for easy iteration
- Signal values shown inline
- Quick actions to create sweeps from single experiments

---

## Implementation Phases

### Phase A: Unified Configuration (Week 1)
1. Merge tabs into single "Experiment Builder"
2. Add sweep checkboxes to epistemic/aleatoric sections
3. Dynamic experiment type detection
4. Smart defaults and warnings

### Phase B: Dashboard Integration (Week 1-2)
1. Move results below configuration
2. Add grouping and filtering
3. Implement "Clone & Sweep" functionality
4. Show signal values inline

### Phase C: Model Selection (Week 2)
1. Add "Use existing checkpoint" option
2. Detect similar configurations
3. Suggest parameter changes
4. Show overlap warnings

### Phase D: Validation Integration (Week 2-3)
1. Show validation status per experiment
2. Heatmap for 2D grids
3. Correlation analysis (Phase 2)
4. Compliance dashboard (Phase 3)

---

## Key UX Principles Applied

### 1. **Progressive Disclosure**
- Start simple, reveal complexity on demand
- Collapsible sections for advanced options
- Smart defaults for common cases

### 2. **Contextual Help**
- Explain CIFAR-10N vs random flipping inline
- Show validation conditions when sweeps enabled
- Warn about duplicate configurations

### 3. **Workflow Continuity**
- Single experiment → 1D sweep → 2D grid in one view
- Clone & Sweep for easy iteration
- Results integrated with configuration

### 4. **Information Density**
- Compact default views
- Expandable details
- Group related experiments
- Show only relevant information

### 5. **Error Prevention**
- Auto-detect experiment type
- Warn about duplicates
- Suggest parameter changes
- Validate before submission

---

## Migration Strategy

### Option 1: Big Bang (Risky)
- Replace all tabs at once
- High risk, high reward
- Requires extensive testing

### Option 2: Gradual (Recommended)
1. Add new "Unified Builder" tab
2. Keep old tabs for comparison
3. Gather user feedback
4. Deprecate old tabs after validation

### Option 3: Hybrid
- Keep Model Selector tab separate
- Merge experiment creation tabs
- Integrate results dashboard

---

## Success Metrics

1. **Time to Create Experiment**: Reduce from 5min → 2min
2. **Configuration Errors**: Reduce by 50%
3. **Sweep Adoption**: Increase 1D/2D sweeps by 3x
4. **User Satisfaction**: Survey score > 4/5

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Create wireframes** for key screens
3. **Prototype** unified builder in separate branch
4. **User testing** with 3-5 researchers
5. **Iterate** based on feedback
6. **Deploy** gradually with feature flag

---

**Recommendation**: Start with Phase A (Unified Configuration) as it provides immediate value and can be implemented in 1 week. The current validation framework (Phase 1) integrates seamlessly into this new design.
