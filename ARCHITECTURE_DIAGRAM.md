# Streamlit Interface Architecture Diagram

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          STREAMLIT APPLICATION                               │
│                         (streamlit_app_v2.py)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│      LAYOUT LAYER                │    │      STATE MANAGEMENT            │
│  (ui_components/layout/)         │    │  (ui_components/shared/)         │
├──────────────────────────────────┤    ├──────────────────────────────────┤
│ • sidebar_advanced.py            │    │ • state_manager.py               │
│ • master_detail_layout.py        │    │ • data_loader.py                 │
│ • responsive_container.py        │    │ • formatters.py                  │
└──────────────────────────────────┘    │ • validators.py                  │
                                        └──────────────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌──────────────────────────────────┐    ┌──────────────────────────────────┐
│   FEATURE COMPONENTS             │    │   VISUALIZATION COMPONENTS       │
├──────────────────────────────────┤    ├──────────────────────────────────┤
│ experiment_browser/              │    │ metrics/                         │
│ • experiment_list.py             │    │ • metrics_dashboard.py           │
│ • experiment_detail.py           │    │ • metrics_cards.py               │
│ • experiment_filters.py          │    │ • metrics_charts.py              │
│ • experiment_actions.py          │    │ • metrics_aggregator.py          │
│                                  │    │                                  │
│ hyperparameters/                 │    │ [Existing Components]            │
│ • parallel_coordinates.py        │    │ • hypothesis_validation.py       │
│ • param_selector.py              │    │ • model_selector.py              │
│ • param_brushing.py              │    │ • signal_diagnostic_viz.py       │
│ • param_export.py                │    │ • per_sample_signals_viz.py      │
└──────────────────────────────────┘    └──────────────────────────────────┘
                    │                                   │
                    └─────────────────┬─────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │      API INTEGRATION LAYER      │
                    │    (HTTP Requests + Cache)      │
                    └─────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │      FASTAPI BACKEND            │
                    │    (localhost:8000)             │
                    ├─────────────────────────────────┤
                    │ • /api/v1/experiments           │
                    │ • /api/v1/datasets              │
                    │ • /api/v1/batch-experiments     │
                    └─────────────────────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │      POSTGRESQL DATABASE        │
                    │    (SQLModel/SQLAlchemy)        │
                    └─────────────────────────────────┘
```

## Component Interaction Flow

### 1. Master-Detail Layout Flow

```
User Action: Click on Experiment
         │
         ▼
┌─────────────────────┐
│  experiment_list.py │
│  (Master Panel)     │
└──────────┬──────────┘
           │ on_select(experiment_id)
           ▼
┌─────────────────────┐
│  state_manager.py   │
│  Update Selection   │
└──────────┬──────────┘
           │ st.session_state['selected_experiment_id']
           ▼
┌─────────────────────┐
│ experiment_detail.py│
│  (Detail Panel)     │
└──────────┬──────────┘
           │ fetch_experiment_details(id)
           ▼
┌─────────────────────┐
│   data_loader.py    │
│   Check Cache       │
└──────────┬──────────┘
           │
           ├─ Cache Hit ──────────┐
           │                      │
           └─ Cache Miss          │
                  │               │
                  ▼               │
           ┌─────────────┐        │
           │ FastAPI GET │        │
           │ /experiments│        │
           │    /{id}    │        │
           └──────┬──────┘        │
                  │               │
                  └───────────────┤
                                  ▼
                          ┌──────────────┐
                          │ Render Detail│
                          │     View     │
                          └──────────────┘
```

### 2. Filter Application Flow

```
User Action: Apply Filter
         │
         ▼
┌─────────────────────┐
│ experiment_filters  │
│      .py            │
└──────────┬──────────┘
           │ on_filter_change(FilterState)
           ▼
┌─────────────────────┐
│  state_manager.py   │
│  Update Filters     │
└──────────┬──────────┘
           │ st.session_state['filter_state']
           ▼
┌─────────────────────┐
│  experiment_list.py │
│  Re-render List     │
└──────────┬──────────┘
           │ Apply filters to cached data
           ▼
┌─────────────────────┐
│  Filtered Results   │
│  (Client-side)      │
└─────────────────────┘
```

### 3. Metrics Dashboard Flow

```
Page Load / Auto-refresh
         │
         ▼
┌─────────────────────┐
│ metrics_dashboard   │
│      .py            │
└──────────┬──────────┘
           │ fetch_metrics()
           ▼
┌─────────────────────┐
│   data_loader.py    │
│   Check Cache       │
└──────────┬──────────┘
           │
           ├─ Cache Valid (TTL: 10s) ──┐
           │                            │
           └─ Cache Expired             │
                  │                     │
                  ▼                     │
           ┌─────────────┐              │
           │ FastAPI GET │              │
           │ /experiments│              │
           └──────┬──────┘              │
                  │                     │
                  └─────────────────────┤
                                        ▼
                                ┌──────────────┐
                                │ metrics_     │
                                │ aggregator.py│
                                └──────┬───────┘
                                       │ Compute metrics
                                       ▼
                                ┌──────────────┐
                                │ metrics_     │
                                │ cards.py     │
                                │ metrics_     │
                                │ charts.py    │
                                └──────────────┘
```

### 4. Parallel Coordinates Flow

```
User Action: Select Parameters
         │
         ▼
┌─────────────────────┐
│  param_selector.py  │
└──────────┬──────────┘
           │ on_param_change(params)
           ▼
┌─────────────────────┐
│  state_manager.py   │
│  Update Selection   │
└──────────┬──────────┘
           │ st.session_state['parcoords_selected_params']
           ▼
┌─────────────────────┐
│ parallel_           │
│ coordinates.py      │
└──────────┬──────────┘
           │ Prepare data for selected params
           ▼
┌─────────────────────┐
│  Plotly Figure      │
│  (Interactive)      │
└──────────┬──────────┘
           │
           ├─ User Brushes Axis ────┐
           │                        │
           └────────────────────────┤
                                    ▼
                            ┌──────────────┐
                            │ param_       │
                            │ brushing.py  │
                            └──────┬───────┘
                                   │ Filter experiments
                                   ▼
                            ┌──────────────┐
                            │ Update       │
                            │ Experiment   │
                            │ List         │
                            └──────────────┘
```

## Data Model Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE SCHEMA                         │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────────────┐
│     User     │         │ UncertaintyExperiment│
├──────────────┤         ├──────────────────────┤
│ id (PK)      │◄────────│ id (PK)              │
│ email        │ 1     * │ name                 │
│ full_name    │         │ config_yaml          │
│ is_active    │         │ status               │
└──────────────┘         │ progress             │
                         │ aleatoric_auroc      │
                         │ epistemic_auroc      │
                         │ results_path         │
                         │ best_signals_json    │
                         │ created_by_id (FK)   │
                         │ created_at           │
                         │ started_at           │
                         │ completed_at         │
                         └──────────────────────┘
                                   │
                                   │
┌──────────────┐                  │
│     User     │                  │
├──────────────┤                  │
│ id (PK)      │◄─────────────────┘
└──────────────┘         1     *
       │                         
       │ 1                       
       │                         
       │ *                       
       ▼                         
┌──────────────────────┐         
│  BatchExperiment     │         
├──────────────────────┤         
│ id (PK)              │         
│ name                 │         
│ description          │         
│ method_type          │         
│ base_config_yaml     │         
│ sweep_definitions    │         
│ status               │         
│ progress             │         
│ total_runs           │         
│ completed_runs       │         
│ created_by_id (FK)   │         
└──────────────────────┘         
       │ 1                       
       │                         
       │ *                       
       ▼                         
┌──────────────────────┐         
│ BatchExperimentRun   │         
├──────────────────────┤         
│ id (PK)              │         
│ batch_id (FK)        │         
│ experiment_id (FK)   │─────────┐
│ run_index            │         │
│ parameter_value      │         │
│ status               │         │
└──────────────────────┘         │
                                 │
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │ UncertaintyExperiment│
                    │ (referenced above)   │
                    └──────────────────────┘
```

## Session State Structure

```
st.session_state
├── user: User
│   ├── id: UUID
│   ├── email: str
│   └── full_name: str
│
├── filter_state: FilterState
│   ├── datasets: List[str]
│   ├── architectures: List[str]
│   ├── statuses: List[JobStatus]
│   ├── date_range: Tuple[datetime, datetime]
│   ├── search_query: str
│   ├── sort_by: str
│   └── sort_order: str
│
├── selected_experiment_ids: List[str]
├── selected_experiment_id: Optional[str]
│
├── experiments_cache: Dict
│   ├── data: List[Dict]
│   ├── timestamp: datetime
│   └── ttl: int (30 seconds)
│
├── metrics_cache: Dict
│   ├── data: Dict
│   ├── timestamp: datetime
│   └── ttl: int (10 seconds)
│
├── ui_state: Dict
│   ├── sidebar_collapsed: bool
│   ├── master_detail_ratio: float (0.3)
│   ├── active_tab: str
│   └── sort_config: Dict
│
├── parcoords_state: Dict
│   ├── selected_params: List[str]
│   ├── color_by: str
│   └── brushed_ranges: Dict[str, Tuple[float, float]]
│
└── loaded_model: Optional[Dict]
    ├── model: Any
    ├── config: Dict
    └── experiment: Dict
```

## Component Dependencies

```
┌─────────────────────────────────────────────────────────────┐
│                    DEPENDENCY GRAPH                          │
└─────────────────────────────────────────────────────────────┘

streamlit_app_v2.py
    │
    ├─► layout/sidebar_advanced.py
    │       └─► shared/state_manager.py
    │       └─► shared/formatters.py
    │       └─► metrics/metrics_cards.py
    │
    ├─► layout/master_detail_layout.py
    │       ├─► experiment_browser/experiment_list.py
    │       │       └─► shared/data_loader.py
    │       │       └─► shared/formatters.py
    │       │       └─► experiment_browser/experiment_filters.py
    │       │
    │       └─► experiment_browser/experiment_detail.py
    │               └─► shared/data_loader.py
    │               └─► shared/formatters.py
    │               └─► experiment_browser/experiment_actions.py
    │
    ├─► metrics/metrics_dashboard.py
    │       ├─► metrics/metrics_cards.py
    │       ├─► metrics/metrics_charts.py
    │       └─► metrics/metrics_aggregator.py
    │               └─► shared/data_loader.py
    │
    ├─► hyperparameters/parallel_coordinates.py
    │       ├─► hyperparameters/param_selector.py
    │       ├─► hyperparameters/param_brushing.py
    │       └─► hyperparameters/param_export.py
    │
    └─► [Existing Components]
            ├─► hypothesis_validation.py
            ├─► model_selector.py
            └─► ...

SHARED UTILITIES (used by all)
    ├─► shared/state_manager.py
    ├─► shared/data_loader.py
    ├─► shared/formatters.py
    └─► shared/validators.py
```

## Caching Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    CACHE HIERARCHY                           │
└─────────────────────────────────────────────────────────────┘

Level 1: Streamlit Cache (@st.cache_data)
    ├─► Static data (datasets, class names)
    ├─► Computed aggregations
    └─► Visualization data
    TTL: Session lifetime or manual invalidation

Level 2: Session Cache (st.session_state)
    ├─► Experiment list
    │   └─► TTL: 30 seconds
    ├─► Metrics data
    │   └─► TTL: 10 seconds
    └─► User preferences
        └─► TTL: Session lifetime

Level 3: Backend Cache (Optional - Redis/in-memory)
    ├─► Database query results
    ├─► Computed metrics
    └─► File system data
    TTL: Configurable per endpoint

Cache Invalidation Triggers:
    ├─► Manual refresh button
    ├─► TTL expiration
    ├─► Experiment completion event
    └─► User logout
```

## Performance Optimization Points

```
┌─────────────────────────────────────────────────────────────┐
│              PERFORMANCE OPTIMIZATION MAP                    │
└─────────────────────────────────────────────────────────────┘

1. Initial Page Load
   ├─► Lazy load heavy components
   ├─► Defer non-critical visualizations
   └─► Use skeleton loaders

2. Experiment List
   ├─► Virtual scrolling (render only visible items)
   ├─► Pagination (50-100 items per page)
   └─► Client-side filtering (no API calls)

3. Detail View
   ├─► Load on demand (not preloaded)
   ├─► Cache loaded experiments
   └─► Progressive loading (tabs load separately)

4. Metrics Dashboard
   ├─► Aggregate on backend
   ├─► Cache with short TTL (10s)
   └─► Debounce auto-refresh

5. Parallel Coordinates
   ├─► Downsample for >1000 points
   ├─► Use WebGL rendering
   └─► Lazy load Plotly library

6. Filters
   ├─► Debounce text input (300ms)
   ├─► Client-side filtering
   └─► Batch state updates
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│                   ERROR HANDLING FLOW                        │
└─────────────────────────────────────────────────────────────┘

API Request
    │
    ├─► Success (200-299)
    │       └─► Update cache
    │       └─► Render component
    │
    ├─► Client Error (400-499)
    │       ├─► 401: Redirect to login
    │       ├─► 403: Show permission error
    │       ├─► 404: Show not found message
    │       └─► Other: Show error toast
    │
    ├─► Server Error (500-599)
    │       └─► Show error message
    │       └─► Offer retry button
    │       └─► Log to console
    │
    └─► Network Error
            └─► Show offline message
            └─► Offer retry button
            └─► Use cached data if available

Component Rendering Error
    │
    └─► Catch with try/except
        └─► Show error boundary
        └─► Log error details
        └─► Offer reload button
        └─► Don't crash entire app
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-03  
**Related:** STREAMLIT_REDESIGN_PLAN.md