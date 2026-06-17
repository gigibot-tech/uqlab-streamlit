# Experiment Tracker Integration Plan for uqlab-streamlit

**Project:** uqlab-streamlit Streamlit Redesign  
**Version:** 1.0  
**Date:** 2026-06-03  
**Status:** Planning Phase

---

## Executive Summary

This document provides a comprehensive analysis of the [CSEM experiment_tracker](https://github.com/csem/experiment_tracker) library and outlines a strategic plan to integrate its components into the uqlab-streamlit Streamlit redesign. The experiment_tracker provides battle-tested components for experiment management, parallel coordinate plots, and data loading that can significantly accelerate our development timeline.

### Key Findings

**✅ Highly Reusable Components:**
- Parallel coordinates plot implementation (ready to use)
- Pandas-based data loading utilities
- Hydra configuration integration patterns

**⚠️ Requires Adaptation:**
- Master-detail layout (not provided, must build custom)
- Advanced filtering (basic filtering exists, needs enhancement)
- Metrics dashboard (not provided, must build custom)
- Backend integration (designed for file-based, needs API adaptation)

**❌ Not Applicable:**
- File-based experiment storage (we use FastAPI + PostgreSQL)
- Hydra-specific folder structure (we have custom backend)

---

## Table of Contents

1. [Experiment Tracker Analysis](#1-experiment-tracker-analysis)
2. [Component Reusability Assessment](#2-component-reusability-assessment)
3. [Integration Architecture](#3-integration-architecture)
4. [Adaptation Strategy](#4-adaptation-strategy)
5. [Backend Integration](#5-backend-integration)
6. [Migration Roadmap](#6-migration-roadmap)
7. [Implementation Plan](#7-implementation-plan)
8. [Risk Assessment](#8-risk-assessment)
9. [Success Criteria](#9-success-criteria)
10. [Conclusion](#10-conclusion)

---

## 1. Experiment Tracker Analysis

### 1.1 Repository Structure

```
experiment_tracker/
├── src/experiment_tracker/
│   ├── __init__.py                    # Main API entry point
│   ├── base_logger.py                 # Logging utilities
│   ├── hydra_utils.py                 # Hydra integration helpers
│   ├── pandas_utils.py                # DataFrame manipulation utilities
│   │
│   ├── gui/                           # Streamlit GUI components
│   │   ├── __init__.py
│   │   ├── dclasses.py                # Data classes (Options)
│   │   ├── gui_utils.py               # Header, SVG rendering
│   │   └── plots.py                   # Plotly visualizations
│   │
│   └── process/                       # Data loading & processing
│       ├── __init__.py
│       ├── base_loader.py             # Abstract base loader
│       ├── dclasses.py                # Data classes
│       ├── file_loader.py             # File-based experiment loader
│       ├── folder_loader.py           # Folder traversal
│       ├── lightning_loader.py        # PyTorch Lightning integration
│       ├── sklearn_gem_loader.py      # Scikit-learn integration
│       └── utils.py                   # Utility functions
```

### 1.2 Core Features

#### ✅ **Parallel Coordinates Plot** (`gui/plots.py`)
- **Function:** `parallel_coordinates(param_df, perf_df)`
- **Features:**
  - Interactive Plotly-based visualization
  - Color-coded by performance metrics
  - Supports categorical and numerical parameters
  - Automatic dimension creation from DataFrame
  - Date/run tracking
  - Random seed grouping
- **Status:** **READY TO USE** with minor adaptations

#### ✅ **Confusion Matrix Visualization** (`gui/plots.py`)
- **Function:** `interactive_confusion_matrix(conf, class_names, ...)`
- **Features:**
  - Interactive heatmap with hover details
  - Percentage or absolute values
  - Customizable colorscale
- **Status:** **READY TO USE**

#### ⚠️ **Data Loading System** (`process/`)
- **Architecture:** File-based with Hydra folder structure
- **Key Classes:**
  - `BaseLoader`: Abstract base for all loaders
  - `FileLoader`: Loads experiments from file system
  - Supports multirun and singlerun modes
- **Status:** **REQUIRES ADAPTATION** for API-based backend

#### ⚠️ **Pandas Utilities** (`pandas_utils.py`)
- **Functions:**
  - `topk()`: Find top-k experiments
  - `groupby_random_seed()`: Group by random seed
  - `find_identical_runs()`: Find duplicate configurations
  - `create_perf_df()`: Create performance DataFrame
- **Status:** **PARTIALLY REUSABLE** (utility functions useful)

#### ❌ **Master-Detail Layout**
- **Status:** **NOT PROVIDED** - Must implement custom

#### ❌ **Advanced Filtering**
- **Status:** **BASIC ONLY** - Example shows simple selectbox filtering
- **Need:** Multi-level, dynamic filtering with search

#### ❌ **Metrics Dashboard**
- **Status:** **NOT PROVIDED** - Must implement custom

### 1.3 Data Model

The experiment_tracker uses a hierarchical pandas DataFrame structure:

```python
# DataFrame Structure (param_df)
MultiIndex Rows:
  - Level 0: Date (e.g., "2021-01-26 17-07-39")
  - Level 1: Run (integer: 0, 1, 2, ...)

Columns:
  - Hydra config parameters (flattened)
  - collected_path_0, collected_path_1, ... (file paths)

# Performance DataFrame (perf_df)
Same MultiIndex as param_df
Columns: metric names (e.g., "epistemic_auroc", "aleatoric_auroc")
```

---

## 2. Component Reusability Assessment

### 2.1 Reusability Matrix

| Component | Reusability | Effort | Priority | Notes |
|-----------|-------------|--------|----------|-------|
| **Parallel Coordinates Plot** | 🟢 High (90%) | Low | P0 | Minor API adaptation needed |
| **Confusion Matrix** | 🟢 High (95%) | Low | P1 | Ready to use as-is |
| **Pandas Utilities** | 🟡 Medium (60%) | Low | P1 | Utility functions useful |
| **Data Loading Pattern** | 🟡 Medium (40%) | Medium | P0 | Concept reusable, implementation not |
| **GUI Header** | 🟢 High (80%) | Low | P2 | Can adapt for branding |
| **Hydra Utils** | 🔴 Low (10%) | N/A | P3 | Not using Hydra |
| **File Loaders** | 🔴 Low (5%) | N/A | P3 | Using FastAPI backend |

### 2.2 Direct Reuse: Parallel Coordinates Plot

**Adaptation for uqlab-streamlit:**

```python
# ui_components/hyperparameters/parallel_coordinates.py

from experiment_tracker.gui.plots import parallel_coordinates as et_parallel_coordinates
import pandas as pd
from typing import List, Dict
import streamlit as st

def render_parallel_coordinates(
    experiments: List[Dict],
    parameters: List[str],
    color_by: str = "epistemic_auroc",
    height: int = 600
) -> None:
    """
    Render parallel coordinates using experiment_tracker.
    
    Converts uqlab-streamlit API data to experiment_tracker format.
    """
    # Convert API response to param_df format
    param_df = _convert_to_param_df(experiments, parameters)
    
    # Convert metrics to perf_df format
    perf_df = _convert_to_perf_df(experiments, [color_by])
    
    # Call experiment_tracker function
    fig = et_parallel_coordinates(param_df, perf_df)
    
    # Customize for uqlab-streamlit
    fig.update_layout(height=height, title="Hyperparameter Exploration")
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)
```

**Benefits:**
- ✅ Proven, production-ready implementation
- ✅ Handles categorical and numerical parameters
- ✅ Interactive brushing/filtering built-in
- ✅ Color-coding by performance metric
- ✅ Saves ~200 lines of complex Plotly code

**Effort:** 2-3 hours (wrapper + conversion functions)

---

## 3. Integration Architecture

### 3.1 Hybrid Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Streamlit App (Main)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────┐  ┌────────────────────────────────────┐  │
│  │  Custom Sidebar  │  │      Main Content Area             │  │
│  │  (uqlab-streamlit)   │  │                                    │  │
│  │                  │  │  ┌──────────────────────────────┐  │  │
│  │ • Filters        │  │  │  Custom Master-Detail        │  │  │
│  │ • Quick Metrics  │  │  │  (uqlab-streamlit)               │  │  │
│  │ • Settings       │  │  │                              │  │  │
│  └──────────────────┘  │  │  ┌────────┬──────────────┐  │  │  │
│                         │  │  │ Master │   Detail     │  │  │  │
│                         │  │  │  List  │    View      │  │  │  │
│                         │  │  └────────┴──────────────┘  │  │  │
│                         │  └──────────────────────────────┘  │  │
│                         │                                    │  │
│                         │  ┌──────────────────────────────┐  │  │
│                         │  │  Custom Metrics Dashboard    │  │  │
│                         │  │  (uqlab-streamlit)               │  │  │
│                         │  └──────────────────────────────┘  │  │
│                         │                                    │  │
│                         │  ┌──────────────────────────────┐  │  │
│                         │  │  Parallel Coordinates        │  │  │
│                         │  │  (experiment_tracker) ✅     │  │  │
│                         │  └──────────────────────────────┘  │  │
│                         └────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  APIExperimentLoader          │
                    │  (Adapter Layer)              │
                    │  • Converts API → DataFrame   │
                    │  • Mimics experiment_tracker  │
                    └───────────────────────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  FastAPI Backend              │
                    │  localhost:8000               │
                    │  • PostgreSQL                 │
                    │  • SQLModel                   │
                    └───────────────────────────────┘
```

---

## 4. Adaptation Strategy

### 4.1 Data Format Conversion

#### uqlab-streamlit API Format:
```json
{
  "id": "exp_123",
  "name": "CNN Dropout Experiment",
  "created_at": "2026-06-03T15:00:00Z",
  "status": "completed",
  "hyperparameters": {
    "epochs": 50,
    "learning_rate": 0.001,
    "hidden_dim": 128,
    "dropout": 0.3
  },
  "results": {
    "epistemic_auroc": 0.85,
    "aleatoric_auroc": 0.78
  }
}
```

#### experiment_tracker DataFrame Format:
```python
# param_df
                              epochs  learning_rate  hidden_dim  dropout
2026-06-03 15-00-00  exp_123  50      0.001         128         0.3

# perf_df
                              epistemic_auroc  aleatoric_auroc
2026-06-03 15-00-00  exp_123  0.85            0.78
```

### 4.2 Conversion Functions

```python
# ui_components/shared/data_converters.py

from typing import List, Dict
import pandas as pd
from datetime import datetime

def api_to_param_df(experiments: List[Dict]) -> pd.DataFrame:
    """Convert API experiments to experiment_tracker param_df format."""
    data = []
    index = []
    
    for exp in experiments:
        timestamp = datetime.fromisoformat(exp['created_at'].replace('Z', '+00:00'))
        timestamp_str = timestamp.strftime("%Y-%m-%d %H-%M-%S")
        exp_id = exp['id']
        index.append((timestamp_str, exp_id))
        
        row = {
            'name': exp['name'],
            'status': exp['status'],
            **exp['hyperparameters']
        }
        data.append(row)
    
    df = pd.DataFrame(data, index=pd.MultiIndex.from_tuples(index))
    df.index.names = ['timestamp', 'experiment_id']
    return df

def api_to_perf_df(experiments: List[Dict]) -> pd.DataFrame:
    """Convert API experiments to experiment_tracker perf_df format."""
    data = []
    index = []
    
    for exp in experiments:
        timestamp = datetime.fromisoformat(exp['created_at'].replace('Z', '+00:00'))
        timestamp_str = timestamp.strftime("%Y-%m-%d %H-%M-%S")
        exp_id = exp['id']
        index.append((timestamp_str, exp_id))
        
        row = exp.get('results', {})
        data.append(row)
    
    df = pd.DataFrame(data, index=pd.MultiIndex.from_tuples(index))
    df.index.names = ['timestamp', 'experiment_id']
    return df
```

---

## 5. Backend Integration

### 5.1 API Adapter Implementation

```python
# ui_components/shared/api_experiment_loader.py

import requests
from typing import List, Dict, Optional, Callable
from datetime import datetime
import pandas as pd

class APIExperimentLoader:
    """
    Adapter that loads experiments from FastAPI backend
    and provides experiment_tracker-compatible interface.
    """
    
    def __init__(self, api_base_url: str, get_headers: Callable[[], Dict]):
        self.api_base_url = api_base_url.rstrip('/')
        self.get_headers = get_headers
    
    def fetch_experiments(
        self,
        filter_status: Optional[str] = None,
        filter_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """Fetch experiments from API."""
        params = {}
        if filter_status:
            params['status'] = filter_status
        if filter_date:
            params['created_after'] = filter_date.isoformat()
        if limit:
            params['limit'] = limit
        
        response = requests.get(
            f"{self.api_base_url}/experiments",
            headers=self.get_headers(),
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    def load_project(
        self,
        filter_status: Optional[str] = None,
        filter_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Load experiments and return in experiment_tracker param_df format.
        Mimics experiment_tracker.load_project() interface.
        """
        experiments = self.fetch_experiments(
            filter_status=filter_status,
            filter_date=filter_date
        )
        
        from .data_converters import api_to_param_df
        return api_to_param_df(experiments)
    
    def load_performance(
        self,
        filter_status: Optional[str] = None
    ) -> pd.DataFrame:
        """Load experiment performance metrics in perf_df format."""
        experiments = self.fetch_experiments(filter_status=filter_status)
        
        from .data_converters import api_to_perf_df
        return api_to_perf_df(experiments)
```

---

## 6. Migration Roadmap

### 6.1 Phase 1: Foundation (Week 1)
**Goal:** Set up experiment_tracker integration infrastructure

**Tasks:**
1. ✅ Clone and install experiment_tracker
2. Create adapter layer (`APIExperimentLoader`)
3. Implement data converters
4. Write unit tests for converters
5. Create example notebook

**Deliverables:**
- `ui_components/shared/api_experiment_loader.py`
- `ui_components/shared/data_converters.py`
- `tests/test_data_converters.py`

**Effort:** 16 hours

### 6.2 Phase 2: Parallel Coordinates Integration (Week 1-2)
**Goal:** Integrate parallel coordinates plot

**Tasks:**
1. Create wrapper component
2. Implement parameter selection UI
3. Add color-by metric selector
4. Test with real data
5. Add export functionality

**Deliverables:**
- `ui_components/hyperparameters/parallel_coordinates.py`
- `ui_components/hyperparameters/param_selector.py`

**Effort:** 8 hours

### 6.3 Phase 3: Utility Functions Integration (Week 2)
**Goal:** Integrate useful pandas utilities

**Tasks:**
1. Create utility wrapper module
2. Integrate `topk()` for best experiments
3. Integrate `find_identical_runs()`
4. Add aggregation functions
5. Document usage patterns

**Effort:** 6 hours

### 6.4 Phase 4: Custom Components (Week 2-4)
**Goal:** Build custom components not provided by experiment_tracker

**Tasks:**
1. Implement master-detail layout (12-16 hours)
2. Implement advanced sidebar (10-12 hours)
3. Implement metrics dashboard (16-20 hours)
4. Implement experiment list (8-10 hours)
5. Implement experiment detail view (10-12 hours)

**Effort:** 56-70 hours (as per original plan)

### 6.5 Phase 5: Integration & Testing (Week 4-5)
**Goal:** Integrate all components and test

**Tasks:**
1. Integrate all components in main app
2. End-to-end testing
3. Performance optimization
4. Bug fixes
5. Documentation

**Effort:** 24 hours

---

## 7. Implementation Plan

### 7.1 Immediate Actions (This Week)

#### Day 1-2: Setup & Adapter Layer
```bash
# Already done:
# 1. Clone experiment_tracker ✅
# 2. Install in editable mode ✅

# Next steps:
mkdir -p uqlab-streamlit/ui_components/shared
touch uqlab-streamlit/ui_components/shared/api_experiment_loader.py
touch uqlab-streamlit/ui_components/shared/data_converters.py
```

#### Day 3-4: Parallel Coordinates Integration
```bash
mkdir -p uqlab-streamlit/ui_components/hyperparameters
touch uqlab-streamlit/ui_components/hyperparameters/parallel_coordinates.py
touch uqlab-streamlit/ui_components/hyperparameters/param_selector.py
```

#### Day 5: Testing & Documentation
```bash
# Write tests and create example notebook
```

### 7.2 Code Templates

#### Template: Parallel Coordinates Wrapper
```python
# ui_components/hyperparameters/parallel_coordinates.py

import streamlit as st
from experiment_tracker.gui.plots import parallel_coordinates as et_parallel_coordinates
from typing import List, Dict

def render_parallel_coordinates(
    experiments: List[Dict],
    parameters: List[str],
    color_by: str = "epistemic_auroc",
    height: int = 600
) -> None:
    """Render interactive parallel coordinates plot."""
    from ui_components.shared.data_converters import api_to_param_df, api_to_perf_df
    
    param_df = api_to_param_df(experiments)
    perf_df = api_to_perf_df(experiments)
    
    param_df_filtered = param_df[parameters]
    perf_df_filtered = perf_df[[color_by]]
    
    fig = et_parallel_coordinates(param_df_filtered, perf_df_filtered)
    fig.update_layout(height=height, title="Hyperparameter Exploration")
    
    st.plotly_chart(fig, use_container_width=True)
```

---

## 8. Risk Assessment

### 8.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Data format incompatibility** | Medium | High | Comprehensive converter testing |
| **Performance issues** | Medium | Medium | Implement pagination; use caching |
| **experiment_tracker API changes** | Low | Medium | Pin version; maintain adapter layer |
| **Integration complexity** | Medium | Medium | Incremental integration; thorough testing |

### 8.2 Mitigation Strategies

1. **Incremental Integration:** Integrate one component at a time
2. **Fallback Plans:** Keep original implementations as backup
3. **Version Pinning:** Pin experiment_tracker version
4. **Comprehensive Testing:** Unit tests, integration tests
5. **Documentation:** Document all adaptations

---

## 9. Success Criteria

### 9.1 Functional Requirements

- ✅ Parallel coordinates plot displays uqlab-streamlit experiments
- ✅ Interactive brushing/filtering works correctly
- ✅ Color-coding by performance metrics functions
- ✅ Data conversion is accurate and complete
- ✅ API adapter handles all experiment types

### 9.2 Non-Functional Requirements

- ✅ Page load time < 3 seconds
- ✅ Parallel coordinates renders in < 2 seconds for 100 experiments
- ✅ No data loss during conversion
- ✅ Code is maintainable and well-documented
- ✅ Tests cover >80% of adapter code

### 9.3 Integration Success Metrics

- **Time Saved:** 20-30 hours (parallel coordinates + utilities)
- **Code Reuse:** ~300 lines of proven code
- **Quality:** Production-tested components
- **Maintainability:** Clear separation between custom and reused code

---

## 10. Conclusion

### 10.1 Summary

The experiment_tracker library provides valuable, production-ready components:

**✅ Direct Benefits:**
- Parallel coordinates plot (saves ~200 lines, 12-16 hours)
- Confusion matrix visualization (saves ~100 lines, 4-6 hours)
- Pandas utilities (saves ~150 lines, 4-6 hours)
- **Total Time Saved: 20-28 hours**

**⚠️ Adaptation Required:**
- API adapter layer (8-10 hours investment)
- Data format converters (4-6 hours investment)
- **Total Investment: 12-16 hours**

**Net Benefit: 8-12 hours saved + proven, tested code**

### 10.2 Recommendations

1. **Proceed with Integration:** Benefits outweigh adaptation costs
2. **Prioritize Parallel Coordinates:** Highest value, lowest effort
3. **Build Robust Adapter:** Invest in solid adapter layer
4. **Maintain Flexibility:** Keep custom implementations as fallback
5. **Document Thoroughly:** Clear documentation of adaptations

### 10.3 Next Steps

**Immediate (This Week):**
1. Implement `APIExperimentLoader` adapter
2. Implement data converters
3. Write unit tests
4. Create example notebook

**Short-term (Next 2 Weeks):**
1. Integrate parallel coordinates
2. Integrate pandas utilities
3. Test with real data
4. Document usage patterns

**Medium-term (Next Month):**
1. Build custom components
2. Full integration testing
3. Performance optimization
4. User acceptance testing

---

## Appendix A: File Structure

```
uqlab-streamlit/
├── ui_components/
│   ├── shared/
│   │   ├── api_experiment_loader.py      # NEW: API adapter
│   │   ├── data_converters.py            # NEW: Format converters
│   │   └── experiment_utils.py           # NEW: Utility wrappers
│   │
│   ├── hyperparameters/
│   │   ├── parallel_coordinates.py       # NEW: experiment_tracker wrapper
│   │   ├── param_selector.py             # NEW: Parameter selection UI
│   │   └── param_export.py               # NEW: Export functionality
│   │
│   ├── layout/
│   │   ├── master_detail_layout.py       # NEW: Custom implementation
│   │   ├── sidebar_advanced.py           # NEW: Custom implementation
│   │   └── responsive_container.py       # NEW: Custom implementation
│   │
│   └── metrics/
│       ├── metrics_dashboard.py          # NEW: Custom implementation
│       ├── metrics_cards.py              # NEW: Custom implementation
│       └── metrics_charts.py             # NEW: Custom implementation
│
├── tests/
│   ├── test_data_converters.py           # NEW: Converter tests
│   ├── test_api_loader.py                # NEW: Adapter tests
│   └── test_parallel_coordinates.py      # NEW: Integration tests
│
└── EXPERIMENT_TRACKER_INTEGRATION_PLAN.md    # THIS DOCUMENT
```

## Appendix B: Dependencies

```toml
# pyproject.toml additions

[project]
dependencies = [
    "experiment-tracker @ git+https://github.com/csem/experiment_tracker.git@main",
]
```

## Appendix C: References

- **experiment_tracker GitHub:** https://github.com/csem/experiment_tracker
- **uqlab-streamlit STREAMLIT_REDESIGN_PLAN:** `uqlab-streamlit/STREAMLIT_REDESIGN_PLAN.md`
- **uqlab-streamlit ARCHITECTURE_DIAGRAM:** `uqlab-streamlit/ARCHITECTURE_DIAGRAM.md`

---

**Document End**