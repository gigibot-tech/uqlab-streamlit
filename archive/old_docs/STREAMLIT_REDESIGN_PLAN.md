# Streamlit Interface Redesign - Implementation Plan

**Project:** uqlab-streamlit Uncertainty Quantification Dashboard  
**Version:** 2.0  
**Date:** 2026-06-03  
**Status:** Planning Phase

---

## Executive Summary

This document outlines a comprehensive plan to redesign the Streamlit interface from a tab-based navigation system to a modern, production-ready dashboard with master-detail layouts, advanced filtering, real-time metrics tracking, and interactive hyperparameter exploration.

### Current State
- **File:** `streamlit_app.py` (241 lines)
- **Architecture:** Tab-based navigation with 3 main tabs
- **Components:** 18+ modular UI components in `ui_components/`
- **Backend:** FastAPI at `http://localhost:8000`
- **Data Models:** SQLModel-based with experiments, batch experiments, and results

### Target State
- **Master-Detail Layout:** Split-screen experiment browser
- **Advanced Sidebar:** Multi-level filtering with quick metrics
- **Metrics Dashboard:** Real-time experiment tracking
- **Parallel Coordinates:** Interactive hyperparameter exploration
- **Modular Architecture:** Clean separation of concerns

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Structure](#2-component-structure)
3. [Implementation Phases](#3-implementation-phases)
4. [Data Flow & State Management](#4-data-flow--state-management)
5. [Migration Strategy](#5-migration-strategy)
6. [Testing Strategy](#6-testing-strategy)
7. [Performance Considerations](#7-performance-considerations)
8. [Backward Compatibility](#8-backward-compatibility)
9. [Deployment Plan](#9-deployment-plan)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit App (Main)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────┐  ┌─────────────────────────────────┐    │
│  │   Advanced    │  │     Main Content Area           │    │
│  │   Sidebar     │  │                                 │    │
│  │               │  │  ┌──────────────────────────┐  │    │
│  │ • Filters     │  │  │   Master-Detail Layout   │  │    │
│  │ • Metrics     │  │  │                          │  │    │
│  │ • Settings    │  │  │  ┌────────┬──────────┐  │  │    │
│  │ • Export      │  │  │  │ Master │  Detail  │  │  │    │
│  │               │  │  │  │  List  │   View   │  │  │    │
│  └───────────────┘  │  │  └────────┴──────────┘  │  │    │
│                      │  └──────────────────────────┘  │    │
│                      │                                 │    │
│                      │  ┌──────────────────────────┐  │    │
│                      │  │   Metrics Dashboard      │  │    │
│                      │  └──────────────────────────┘  │    │
│                      │                                 │    │
│                      │  ┌──────────────────────────┐  │    │
│                      │  │  Parallel Coordinates    │  │    │
│                      │  └──────────────────────────┘  │    │
│                      └─────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  FastAPI Backend │
                    │  localhost:8000  │
                    └──────────────────┘
```

### 1.2 Component Hierarchy

```
streamlit_app.py (Main Entry Point)
│
├── ui_components/
│   ├── layout/
│   │   ├── sidebar_advanced.py          # Advanced sidebar with filters
│   │   ├── master_detail_layout.py      # Split-screen layout manager
│   │   └── responsive_container.py      # Responsive wrapper utilities
│   │
│   ├── experiment_browser/
│   │   ├── experiment_list.py           # Master list with filtering
│   │   ├── experiment_detail.py         # Detail view for selected experiment
│   │   ├── experiment_filters.py        # Filter components
│   │   └── experiment_actions.py        # Action buttons (run, delete, export)
│   │
│   ├── metrics/
│   │   ├── metrics_dashboard.py         # Real-time metrics overview
│   │   ├── metrics_cards.py             # Individual metric cards
│   │   ├── metrics_charts.py            # Time-series and trend charts
│   │   └── metrics_aggregator.py        # Data aggregation logic
│   │
│   ├── hyperparameters/
│   │   ├── parallel_coordinates.py      # Main parallel coord plot
│   │   ├── param_selector.py            # Parameter selection UI
│   │   ├── param_brushing.py            # Interactive brushing/filtering
│   │   └── param_export.py              # Export functionality
│   │
│   ├── shared/
│   │   ├── data_loader.py               # Centralized data fetching
│   │   ├── state_manager.py             # Session state management
│   │   ├── formatters.py                # Data formatting utilities
│   │   └── validators.py                # Input validation
│   │
│   └── [existing components...]         # Keep current components
│       ├── hypothesis_validation.py
│       ├── model_selector.py
│       └── ...
```

---

## 2. Component Structure

### 2.1 Advanced Sidebar Component

**File:** `ui_components/layout/sidebar_advanced.py`

**Features:**
- Multi-level filtering (dataset, architecture, status, date range)
- Quick metrics overview (total runs, success rate, avg duration)
- Export/download options
- Settings/preferences
- Collapsible sections

**API:**
```python
def render_advanced_sidebar(
    experiments: List[Dict],
    on_filter_change: Callable[[FilterState], None]
) -> FilterState:
    """
    Render advanced sidebar with filtering and metrics.
    
    Args:
        experiments: List of all experiments
        on_filter_change: Callback when filters change
        
    Returns:
        FilterState object with current filter selections
    """
```

**Filter State Structure:**
```python
@dataclass
class FilterState:
    datasets: List[str]
    architectures: List[str]
    statuses: List[JobStatus]
    date_range: Tuple[datetime, datetime]
    search_query: str
    sort_by: str
    sort_order: str  # 'asc' or 'desc'
```

### 2.2 Master-Detail Layout Component

**File:** `ui_components/layout/master_detail_layout.py`

**Features:**
- Adjustable split ratio (default 30/70)
- Responsive design (stacks on mobile)
- Synchronized scrolling
- Keyboard navigation support

**API:**
```python
def render_master_detail_layout(
    master_content: Callable[[], None],
    detail_content: Callable[[Optional[str]], None],
    split_ratio: float = 0.3,
    selected_id: Optional[str] = None
) -> Optional[str]:
    """
    Render master-detail split layout.
    
    Args:
        master_content: Function to render master list
        detail_content: Function to render detail view
        split_ratio: Ratio of master to total width (0.0-1.0)
        selected_id: Currently selected item ID
        
    Returns:
        Selected item ID (may change based on user interaction)
    """
```

### 2.3 Experiment Browser Components

**File:** `ui_components/experiment_browser/experiment_list.py`

**Features:**
- Virtualized list for performance
- Multi-select support
- Inline status indicators
- Quick actions (run, pause, delete)
- Sorting and grouping

**API:**
```python
def render_experiment_list(
    experiments: List[Dict],
    filters: FilterState,
    selected_ids: List[str],
    on_select: Callable[[List[str]], None]
) -> None:
    """
    Render filterable experiment list.
    
    Args:
        experiments: List of experiments to display
        filters: Current filter state
        selected_ids: Currently selected experiment IDs
        on_select: Callback when selection changes
    """
```

**File:** `ui_components/experiment_browser/experiment_detail.py`

**Features:**
- Tabbed detail view (Overview, Config, Results, Logs)
- Inline editing of experiment name/description
- Quick actions (rerun, clone, export)
- Related experiments section

**API:**
```python
def render_experiment_detail(
    experiment_id: str,
    api_base_url: str,
    get_headers: Callable[[], Dict]
) -> None:
    """
    Render detailed view of selected experiment.
    
    Args:
        experiment_id: ID of experiment to display
        api_base_url: Base URL for API requests
        get_headers: Function to get request headers
    """
```

### 2.4 Metrics Dashboard Component

**File:** `ui_components/metrics/metrics_dashboard.py`

**Features:**
- Real-time experiment status overview
- Performance metrics visualization
- Resource usage tracking
- Historical trends
- Customizable metric cards

**API:**
```python
def render_metrics_dashboard(
    experiments: List[Dict],
    time_range: str = "24h",
    refresh_interval: int = 30
) -> None:
    """
    Render real-time metrics dashboard.
    
    Args:
        experiments: List of experiments to analyze
        time_range: Time range for metrics ('1h', '24h', '7d', '30d')
        refresh_interval: Auto-refresh interval in seconds
    """
```

**Metrics to Track:**
- Total experiments (all time, today, this week)
- Success rate (percentage)
- Average duration
- Active experiments
- Failed experiments (with error categories)
- AUROC trends (epistemic, aleatoric)
- Resource utilization (if available)

### 2.5 Parallel Coordinates Component

**File:** `ui_components/hyperparameters/parallel_coordinates.py`

**Features:**
- Interactive parallel coordinate plot
- Color-coded by performance metric
- Brushing/filtering on axes
- Hover tooltips with details
- Export to image/data

**API:**
```python
def render_parallel_coordinates(
    experiments: List[Dict],
    parameters: List[str],
    color_by: str = "epistemic_auroc",
    height: int = 600
) -> None:
    """
    Render interactive parallel coordinates plot.
    
    Args:
        experiments: List of experiments with hyperparameters
        parameters: List of parameter names to display
        color_by: Metric to use for color coding
        height: Plot height in pixels
    """
```

**Supported Parameters:**
- `epochs`
- `learning_rate`
- `hidden_dim`
- `dropout`
- `train_batch_size`
- `mc_passes`
- `under_train_per_class`
- `regular_train_per_class`

---

## 3. Implementation Phases

### Phase 1: Architecture & Design (Week 1)
**Status:** Planning  
**Duration:** 3-5 days

**Tasks:**
1. ✅ Review current codebase and identify reusable components
2. ✅ Define component interfaces and data contracts
3. ✅ Create component hierarchy diagram
4. ✅ Design state management strategy
5. ✅ Document API specifications
6. Create wireframes for each major component
7. Review and approve architecture with stakeholders

**Deliverables:**
- Architecture document (this file)
- Component API specifications
- Wireframes/mockups
- State management design

### Phase 2: Core Infrastructure (Week 1-2)
**Status:** Not Started  
**Duration:** 5-7 days

**Tasks:**
1. Create `ui_components/layout/` directory structure
2. Implement `state_manager.py` for centralized state
3. Implement `data_loader.py` for API interactions
4. Create `formatters.py` and `validators.py` utilities
5. Build `responsive_container.py` for layout management
6. Write unit tests for core utilities
7. Document usage patterns

**Deliverables:**
- Core infrastructure components
- Unit tests (>80% coverage)
- Usage documentation

**Dependencies:**
- None (foundational work)

### Phase 3: Master-Detail Layout (Week 2)
**Status:** Not Started  
**Duration:** 4-6 days

**Tasks:**
1. Implement `master_detail_layout.py` component
2. Create `experiment_list.py` with filtering
3. Create `experiment_detail.py` with tabs
4. Implement `experiment_filters.py` UI
5. Add keyboard navigation support
6. Test responsive behavior
7. Integrate with existing data sources

**Deliverables:**
- Master-detail layout component
- Experiment browser components
- Integration tests
- User guide

**Dependencies:**
- Phase 2 (Core Infrastructure)

### Phase 4: Advanced Sidebar (Week 2-3)
**Status:** Not Started  
**Duration:** 3-5 days

**Tasks:**
1. Implement `sidebar_advanced.py` component
2. Create multi-level filter UI
3. Add quick metrics overview cards
4. Implement export functionality
5. Add settings/preferences panel
6. Test filter performance with large datasets
7. Document filter API

**Deliverables:**
- Advanced sidebar component
- Filter system
- Export functionality
- Performance benchmarks

**Dependencies:**
- Phase 2 (Core Infrastructure)
- Phase 3 (for filter integration)

### Phase 5: Metrics Dashboard (Week 3)
**Status:** Not Started  
**Duration:** 5-7 days

**Tasks:**
1. Implement `metrics_dashboard.py` component
2. Create `metrics_cards.py` for individual metrics
3. Build `metrics_charts.py` for visualizations
4. Implement `metrics_aggregator.py` for data processing
5. Add real-time refresh capability
6. Create time-range selector
7. Test with historical data

**Deliverables:**
- Metrics dashboard component
- Real-time tracking system
- Visualization components
- Aggregation logic

**Dependencies:**
- Phase 2 (Core Infrastructure)
- Backend API for metrics data

### Phase 6: Parallel Coordinates (Week 3-4)
**Status:** Not Started  
**Duration:** 5-7 days

**Tasks:**
1. Implement `parallel_coordinates.py` using Plotly
2. Create `param_selector.py` for parameter selection
3. Implement `param_brushing.py` for interactive filtering
4. Add `param_export.py` for data/image export
5. Optimize rendering for large datasets
6. Add color schemes and customization
7. Test interaction performance

**Deliverables:**
- Parallel coordinates component
- Interactive filtering system
- Export functionality
- Performance optimizations

**Dependencies:**
- Phase 2 (Core Infrastructure)
- Plotly library

### Phase 7: Integration & Migration (Week 4)
**Status:** Not Started  
**Duration:** 5-7 days

**Tasks:**
1. Create new `streamlit_app_v2.py` entry point
2. Integrate all new components
3. Migrate existing functionality
4. Update routing and navigation
5. Test end-to-end workflows
6. Fix integration issues
7. Performance tuning

**Deliverables:**
- Integrated application
- Migration guide
- Integration tests
- Performance report

**Dependencies:**
- All previous phases

### Phase 8: Testing & Performance (Week 4-5)
**Status:** Not Started  
**Duration:** 4-6 days

**Tasks:**
1. Comprehensive functional testing
2. Performance testing with large datasets
3. Browser compatibility testing
4. Accessibility testing
5. Load testing
6. Bug fixes and optimizations
7. User acceptance testing

**Deliverables:**
- Test reports
- Performance benchmarks
- Bug fix list
- Optimization recommendations

**Dependencies:**
- Phase 7 (Integration)

### Phase 9: Documentation & Deployment (Week 5)
**Status:** Not Started  
**Duration:** 3-5 days

**Tasks:**
1. Write user documentation
2. Create developer guide
3. Record demo videos
4. Prepare deployment scripts
5. Create rollback plan
6. Deploy to staging
7. Deploy to production

**Deliverables:**
- User documentation
- Developer guide
- Demo videos
- Deployment scripts
- Rollback plan

**Dependencies:**
- Phase 8 (Testing)

---

## 4. Data Flow & State Management

### 4.1 State Management Strategy

**Session State Structure:**
```python
st.session_state = {
    # User & Auth
    'user': User,
    'api_token': str,
    
    # Filters & Selection
    'filter_state': FilterState,
    'selected_experiment_ids': List[str],
    'selected_experiment_id': Optional[str],  # For detail view
    
    # Data Cache
    'experiments_cache': {
        'data': List[Dict],
        'timestamp': datetime,
        'ttl': int  # seconds
    },
    'metrics_cache': {
        'data': Dict,
        'timestamp': datetime,
        'ttl': int
    },
    
    # UI State
    'sidebar_collapsed': bool,
    'master_detail_ratio': float,
    'active_tab': str,
    'sort_config': Dict,
    
    # Parallel Coordinates
    'parcoords_selected_params': List[str],
    'parcoords_color_by': str,
    'parcoords_brushed_ranges': Dict[str, Tuple[float, float]],
    
    # Loaded Models (existing)
    'loaded_model': Optional[Any],
    'loaded_model_config': Optional[Dict],
    'loaded_model_experiment': Optional[Dict],
}
```

### 4.2 Data Flow Diagram

```
┌──────────────┐
│   User       │
│  Interaction │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│  UI Component    │
│  (Streamlit)     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐      ┌─────────────────┐
│  State Manager   │◄────►│ Session State   │
└──────┬───────────┘      └─────────────────┘
       │
       ▼
┌──────────────────┐      ┌─────────────────┐
│  Data Loader     │◄────►│  Cache Layer    │
└──────┬───────────┘      └─────────────────┘
       │
       ▼
┌──────────────────┐
│  FastAPI Backend │
│  (REST API)      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   PostgreSQL     │
│   Database       │
└──────────────────┘
```

### 4.3 Caching Strategy

**Cache Levels:**

1. **Session Cache** (in-memory, per user session)
   - Experiment list (TTL: 30 seconds)
   - Metrics data (TTL: 10 seconds)
   - User preferences (TTL: session lifetime)

2. **Streamlit Cache** (`@st.cache_data`)
   - Static data (datasets, class names)
   - Computed aggregations
   - Visualization data

3. **Backend Cache** (Redis/in-memory)
   - Database query results
   - Computed metrics
   - File system data

**Cache Invalidation:**
- Manual refresh button
- Automatic TTL expiration
- Event-based invalidation (on experiment completion)

---

## 5. Migration Strategy

### 5.1 Phased Migration Approach

**Option A: Parallel Development (Recommended)**
1. Keep `streamlit_app.py` as-is
2. Create `streamlit_app_v2.py` with new design
3. Add toggle in UI to switch between versions
4. Gradual migration of users
5. Deprecate v1 after validation period

**Option B: In-Place Migration**
1. Create feature flags for new components
2. Gradually replace old components
3. Test each replacement thoroughly
4. Remove old code after validation

**Recommendation:** Use Option A for safety and easier rollback.

### 5.2 Component Mapping

| Current Component | New Component | Migration Strategy |
|-------------------|---------------|-------------------|
| Tab-based navigation | Master-detail layout | Replace entirely |
| Simple sidebar | Advanced sidebar | Enhance existing |
| Experiment list (in tabs) | Experiment browser | Refactor and enhance |
| Results display | Metrics dashboard | New component |
| N/A | Parallel coordinates | New component |
| `hypothesis_validation.py` | Keep as-is | Integrate into new layout |
| `model_selector.py` | Keep as-is | Integrate into new layout |
| Other UI components | Keep as-is | Integrate as needed |

### 5.3 Data Migration

**No database migration required** - all changes are UI-only.

**Configuration Migration:**
- User preferences stored in session state
- No persistent storage changes needed
- Backward compatible with existing API

### 5.4 Rollback Plan

**If issues arise:**
1. Toggle feature flag to disable v2
2. Redirect users to `streamlit_app.py` (v1)
3. Investigate and fix issues
4. Re-enable v2 after validation

**Rollback triggers:**
- Critical bugs affecting >10% of users
- Performance degradation >50%
- Data integrity issues
- Security vulnerabilities

---

## 6. Testing Strategy

### 6.1 Unit Testing

**Framework:** pytest + pytest-streamlit

**Coverage Target:** >80%

**Test Categories:**
1. **Component Tests**
   - Render without errors
   - Handle empty data
   - Handle large datasets
   - Validate prop types

2. **Utility Tests**
   - Data formatting
   - Validation logic
   - State management
   - Cache operations

3. **Integration Tests**
   - Component interactions
   - API calls
   - State synchronization
   - Error handling

**Example Test:**
```python
def test_experiment_list_renders_empty():
    """Test experiment list handles empty data gracefully."""
    from ui_components.experiment_browser.experiment_list import render_experiment_list
    
    experiments = []
    filters = FilterState()
    selected_ids = []
    
    # Should not raise exception
    render_experiment_list(experiments, filters, selected_ids, lambda x: None)
```

### 6.2 Integration Testing

**Test Scenarios:**
1. End-to-end experiment creation and viewing
2. Filter application and result updates
3. Master-detail synchronization
4. Metrics dashboard refresh
5. Parallel coordinates interaction
6. Export functionality

**Tools:**
- Selenium for browser automation
- pytest for test orchestration
- Mock API responses for isolation

### 6.3 Performance Testing

**Metrics to Track:**
- Initial page load time (<3 seconds)
- Component render time (<500ms)
- Filter application time (<200ms)
- Large dataset handling (1000+ experiments)
- Memory usage (<500MB for typical session)

**Tools:**
- Streamlit profiler
- Python cProfile
- Browser DevTools

**Load Testing:**
- Simulate 10 concurrent users
- Test with 5000+ experiments
- Measure response times under load

### 6.4 User Acceptance Testing

**Test Plan:**
1. Recruit 5-10 beta testers
2. Provide test scenarios
3. Collect feedback via survey
4. Conduct usability interviews
5. Iterate based on feedback

**Test Scenarios:**
- Create and run an experiment
- Filter experiments by multiple criteria
- View experiment details
- Analyze hyperparameter trends
- Export results

---

## 7. Performance Considerations

### 7.1 Optimization Strategies

**1. Lazy Loading**
- Load experiment details only when selected
- Defer loading of heavy visualizations
- Paginate large lists

**2. Virtualization**
- Use virtual scrolling for long lists
- Render only visible items
- Implement windowing for tables

**3. Caching**
- Cache API responses
- Memoize expensive computations
- Use Streamlit's `@st.cache_data`

**4. Debouncing**
- Debounce filter inputs (300ms)
- Throttle scroll events
- Batch state updates

**5. Code Splitting**
- Lazy import heavy libraries
- Split components into separate files
- Use dynamic imports where possible

### 7.2 Performance Targets

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Initial Load | <2s | <3s | >3s |
| Filter Apply | <200ms | <500ms | >500ms |
| Detail View Load | <500ms | <1s | >1s |
| Chart Render | <1s | <2s | >2s |
| Memory Usage | <300MB | <500MB | >500MB |

### 7.3 Monitoring

**Metrics to Track:**
- Page load times
- Component render times
- API response times
- Error rates
- User session duration

**Tools:**
- Streamlit built-in metrics
- Custom timing decorators
- Application logs
- User analytics (optional)

---

## 8. Backward Compatibility

### 8.1 API Compatibility

**No breaking changes to backend API required.**

All new features use existing endpoints:
- `GET /api/v1/experiments/no-auth` - List experiments
- `GET /api/v1/experiments/{id}` - Get experiment details
- `POST /api/v1/experiments` - Create experiment
- `GET /api/v1/datasets/{name}/stats` - Get dataset stats

**New endpoints (optional enhancements):**
- `GET /api/v1/metrics/dashboard` - Aggregated metrics
- `GET /api/v1/experiments/search` - Advanced search
- `GET /api/v1/experiments/export` - Bulk export

### 8.2 Data Model Compatibility

**No changes to database schema required.**

Existing tables remain unchanged:
- `user`
- `uncertainty_experiment`
- `batch_experiment`
- `batch_experiment_run`

**Optional enhancements:**
- Add indexes for common queries
- Add materialized views for metrics
- Add audit logging table

### 8.3 Component Compatibility

**Existing components remain functional:**
- `hypothesis_validation.py` - Integrate into new layout
- `model_selector.py` - Integrate into new layout
- `uq_benchmarks.py` - Integrate into new layout
- All other components - Available in new UI

**Migration path:**
- Old components work in new layout
- Gradual enhancement of components
- No forced migration

---

## 9. Deployment Plan

### 9.1 Pre-Deployment Checklist

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Performance benchmarks met
- [ ] User acceptance testing complete
- [ ] Documentation complete
- [ ] Rollback plan tested
- [ ] Stakeholder approval obtained

### 9.2 Deployment Steps

**Step 1: Staging Deployment**
1. Deploy to staging environment
2. Run smoke tests
3. Conduct final UAT
4. Fix any critical issues
5. Get sign-off from stakeholders

**Step 2: Canary Deployment**
1. Deploy to 10% of users
2. Monitor metrics for 24 hours
3. Collect user feedback
4. Fix any issues
5. Expand to 50% if successful

**Step 3: Full Deployment**
1. Deploy to all users
2. Monitor metrics for 48 hours
3. Provide user support
4. Collect feedback
5. Plan next iteration

### 9.3 Rollback Procedure

**If critical issues arise:**

1. **Immediate Actions** (within 5 minutes)
   - Toggle feature flag to disable v2
   - Redirect to v1 interface
   - Notify users of temporary rollback

2. **Investigation** (within 1 hour)
   - Identify root cause
   - Assess impact
   - Determine fix timeline

3. **Resolution** (within 24 hours)
   - Implement fix
   - Test thoroughly
   - Deploy fix to staging
   - Re-enable v2 after validation

### 9.4 Post-Deployment

**Week 1:**
- Daily monitoring of metrics
- Rapid response to user issues
- Collect user feedback
- Hot-fix critical bugs

**Week 2-4:**
- Weekly metric reviews
- User feedback analysis
- Plan enhancements
- Optimize performance

**Month 2+:**
- Deprecate v1 interface
- Remove old code
- Document lessons learned
- Plan next features

---

## 10. File Structure

### 10.1 New Directory Structure

```
uqlab-streamlit/
├── streamlit_app.py                    # Current v1 (keep for now)
├── streamlit_app_v2.py                 # New v2 entry point
├── ui_components/
│   ├── __init__.py
│   │
│   ├── layout/                         # NEW: Layout components
│   │   ├── __init__.py
│   │   ├── sidebar_advanced.py
│   │   ├── master_detail_layout.py
│   │   └── responsive_container.py
│   │
│   ├── experiment_browser/             # NEW: Experiment browsing
│   │   ├── __init__.py
│   │   ├── experiment_list.py
│   │   ├── experiment_detail.py
│   │   ├── experiment_filters.py
│   │   └── experiment_actions.py
│   │
│   ├── metrics/                        # NEW: Metrics dashboard
│   │   ├── __init__.py
│   │   ├── metrics_dashboard.py
│   │   ├── metrics_cards.py
│   │   ├── metrics_charts.py
│   │   └── metrics_aggregator.py
│   │
│   ├── hyperparameters/                # NEW: Hyperparameter viz
│   │   ├── __init__.py
│   │   ├── parallel_coordinates.py
│   │   ├── param_selector.py
│   │   ├── param_brushing.py
│   │   └── param_export.py
│   │
│   ├── shared/                         # NEW: Shared utilities
│   │   ├── __init__.py
│   │   ├── data_loader.py
│   │   ├── state_manager.py
│   │   ├── formatters.py
│   │   └── validators.py
│   │
│   └── [existing components...]        # KEEP: Existing components
│       ├── hypothesis_validation.py
│       ├── model_selector.py
│       ├── per_sample_signals_viz.py
│       ├── signal_diagnostic_viz.py
│       └── ...
│
├── tests/                              # NEW: Test suite
│   ├── unit/
│   │   ├── test_layout_components.py
│   │   ├── test_experiment_browser.py
│   │   ├── test_metrics.py
│   │   └── test_hyperparameters.py
│   ├── integration/
│   │   ├── test_end_to_end.py
│   │   └── test_api_integration.py
│   └── performance/
│       └── test_performance.py
│
└── docs/                               # NEW: Documentation
    ├── user_guide.md
    ├── developer_guide.md
    ├── api_reference.md
    └── migration_guide.md
```

### 10.2 Component Size Estimates

| Component | Estimated Lines | Complexity |
|-----------|----------------|------------|
| `sidebar_advanced.py` | 200-300 | Medium |
| `master_detail_layout.py` | 150-200 | Medium |
| `experiment_list.py` | 250-350 | High |
| `experiment_detail.py` | 300-400 | High |
| `experiment_filters.py` | 150-200 | Medium |
| `metrics_dashboard.py` | 200-300 | Medium |
| `metrics_charts.py` | 250-350 | High |
| `parallel_coordinates.py` | 300-400 | High |
| `data_loader.py` | 200-250 | Medium |
| `state_manager.py` | 150-200 | Medium |
| **Total New Code** | **~2500-3500** | - |

---

## 11. Dependencies

### 11.1 Python Packages

**Existing:**
- `streamlit>=1.28.0`
- `requests>=2.31.0`
- `pandas>=2.0.0`
- `plotly>=5.17.0`
- `pydantic>=2.0.0`

**New (if needed):**
- `streamlit-aggrid>=0.3.4` - For advanced tables
- `streamlit-extras>=0.3.0` - For additional UI components
- `cachetools>=5.3.0` - For advanced caching

### 11.2 Browser Requirements

**Minimum:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Recommended:**
- Chrome 100+
- Firefox 100+
- Safari 15+
- Edge 100+

---

## 12. Risk Assessment

### 12.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance degradation with large datasets | Medium | High | Implement virtualization, pagination, caching |
| Browser compatibility issues | Low | Medium | Test on all major browsers, use polyfills |
| State management complexity | Medium | Medium | Use proven patterns, thorough testing |
| Integration issues with existing code | Low | High | Parallel development, gradual migration |
| API rate limiting | Low | Medium | Implement caching, batch requests |

### 12.2 Project Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Timeline delays | Medium | Medium | Buffer time in schedule, prioritize features |
| Scope creep | High | High | Strict change control, MVP focus |
| Resource availability | Low | High | Cross-training, documentation |
| User resistance to change | Medium | Medium | User training, gradual rollout |
| Incomplete requirements | Low | Medium | Regular stakeholder reviews |

---

## 13. Success Criteria

### 13.1 Functional Requirements

- [ ] Master-detail layout displays experiments correctly
- [ ] Filters work across all dimensions
- [ ] Metrics dashboard shows real-time data
- [ ] Parallel coordinates plot is interactive
- [ ] All existing features remain functional
- [ ] Export functionality works correctly

### 13.2 Non-Functional Requirements

- [ ] Page load time <3 seconds
- [ ] Filter application <500ms
- [ ] Handles 1000+ experiments smoothly
- [ ] Works on all major browsers
- [ ] Mobile-responsive design
- [ ] Accessibility compliant (WCAG 2.1 AA)

### 13.3 User Satisfaction

- [ ] >80% user satisfaction score
- [ ] <5% rollback requests
- [ ] >90% feature adoption rate
- [ ] Positive feedback on usability
- [ ] Reduced time to complete common tasks

---

## 14. Next Steps

### Immediate Actions (This Week)

1. **Review and approve this plan** with stakeholders
2. **Set up development environment** for new components
3. **Create project board** with all tasks
4. **Assign team members** to phases
5. **Schedule kickoff meeting** for Phase 2

### Short-term (Next 2 Weeks)

1. Complete Phase 2 (Core Infrastructure)
2. Begin Phase 3 (Master-Detail Layout)
3. Set up CI/CD for automated testing
4. Create initial wireframes/mockups
5. Begin documentation

### Medium-term (Next Month)

1. Complete Phases 3-6 (all major components)
2. Begin integration testing
3. Conduct internal demos
4. Gather feedback and iterate
5. Prepare for staging deployment

### Long-term (Next 2 Months)

1. Complete testing and optimization
2. Deploy to staging
3. Conduct UAT
4. Deploy to production
5. Monitor and iterate

---

## 15. Appendix

### A. Glossary

- **Master-Detail Layout:** UI pattern with list view (master) and detail view
- **Parallel Coordinates:** Visualization for multivariate data
- **AUROC:** Area Under Receiver Operating Characteristic curve
- **Epistemic Uncertainty:** Model uncertainty (lack of knowledge)
- **Aleatoric Uncertainty:** Data uncertainty (inherent noise)
- **UDE:** Uncertainty Disentanglement Error

### B. References

- Streamlit Documentation: https://docs.streamlit.io
- Plotly Parallel Coordinates: https://plotly.com/python/parallel-coordinates-plot/
- FastAPI Documentation: https://fastapi.tiangolo.com
- SQLModel Documentation: https://sqlmodel.tiangolo.com

### C. Contact Information

- **Project Lead:** [Name]
- **Technical Lead:** [Name]
- **Product Owner:** [Name]
- **Stakeholders:** [Names]

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-03  
**Next Review:** 2026-06-10
