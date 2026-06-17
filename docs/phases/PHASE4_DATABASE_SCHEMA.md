# Phase 4: Database Schema - Complete ✅

## Overview

Phase 4 successfully adds database tables for storing UQ benchmark results, following the **additive-only** principle to maintain backward compatibility with the existing system.

## What Was Built

### 1. New Database Tables (`backend/app/tables.py`)

#### Table: `BenchmarkResult`
Stores individual benchmark experiment results.

**Purpose**: Track results from single UQ method evaluations

**Schema**:
```python
class BenchmarkResult(SQLModel, table=True):
    id: uuid.UUID                    # Primary key
    method: str                      # UQ method name (indexed)
    framework: str                   # "keras" or "pytorch"
    
    # Configuration (JSON for flexibility)
    dataset_config_json: str
    training_config_json: str
    evaluation_config_json: str
    
    # Results
    accuracy: float
    aleatoric_uncertainty: float
    epistemic_uncertainty: float
    
    # Performance metrics
    training_time: float             # seconds
    evaluation_time: float           # seconds
    
    # Status tracking
    status: JobStatus
    error_message: str | None
    
    # Timestamps
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    
    # Relationships
    created_by_id: uuid.UUID         # FK to User
    sweep_id: uuid.UUID | None       # Optional FK to BenchmarkSweep
```

**Indexes**:
- `idx_benchmarkresult_method`: Fast queries by method
- `idx_benchmarkresult_created_by`: Fast queries by user
- `idx_benchmarkresult_sweep`: Fast queries by sweep

#### Table: `BenchmarkSweep`
Stores parameter sweep experiments.

**Purpose**: Track multi-run experiments that sweep a single parameter

**Schema**:
```python
class BenchmarkSweep(SQLModel, table=True):
    id: uuid.UUID                    # Primary key
    name: str
    description: str | None
    
    # Sweep configuration
    method: str                      # UQ method (indexed)
    sweep_parameter: str             # e.g., "noise_rate"
    sweep_values_json: str           # JSON array of values
    base_config_json: str            # Non-swept parameters
    
    # Aggregate status
    status: JobStatus
    progress: float                  # 0-100
    total_runs: int
    completed_runs: int
    failed_runs: int
    
    # Timestamps
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    
    # Relationships
    created_by_id: uuid.UUID         # FK to User
    results: list[BenchmarkResult]   # One-to-many
```

**Indexes**:
- `idx_benchmarksweep_method`: Fast queries by method
- `idx_benchmarksweep_created_by`: Fast queries by user
- `idx_benchmarksweep_status`: Fast queries by status

### 2. User Model Updates

Added new relationships to the `User` model:

```python
class User(SQLModel, table=True):
    # ... existing fields ...
    
    # New UQ Benchmarks relationships (Phase 4)
    benchmark_results: list["BenchmarkResult"] = Relationship(cascade_delete=True)
    benchmark_sweeps: list["BenchmarkSweep"] = Relationship(cascade_delete=True)
```

### 3. Migration Scripts

#### SQL Migration (`backend/migrations/add_benchmark_tables.sql`)
- Creates both tables with proper indexes
- SQLite compatible
- Includes comprehensive documentation

#### Python Migration Runner (`backend/run_benchmark_migration.py`)
- Automated migration execution
- Verification of table creation
- Error handling and rollback

### 4. Updated API Routes

Modified `backend/app/api/routes/uq_benchmarks.py` to import new tables:
```python
from app.tables import BenchmarkResult, BenchmarkSweep, JobStatus
```

Ready for storing results in Phase 5.

## Design Decisions

### 1. ✅ Additive Only - Zero Breaking Changes

**No modifications to existing tables**:
- `UncertaintyExperiment` unchanged
- `BatchExperiment` unchanged
- `BatchExperimentRun` unchanged
- All existing experiments continue to work

**Only additions**:
- 2 new tables
- 2 new User relationships
- New indexes

### 2. ✅ JSON Configuration Storage

**Why JSON for configs?**
- **Flexibility**: Schema can evolve without migrations
- **Complete audit trail**: Full configuration stored
- **Easy debugging**: See exact parameters used
- **Framework agnostic**: Works with any UQ method

**What's stored as JSON**:
```json
{
  "dataset_config_json": {
    "under_supported_classes": [3, 5],
    "under_train_per_class": 50,
    "regular_train_per_class": 300,
    "noise_rate": 0.2,
    "test_mode": true
  },
  "training_config_json": {
    "epochs": 10,
    "batch_size": 32,
    "learning_rate": 0.001
  },
  "evaluation_config_json": {
    "mc_passes": 20
  }
}
```

### 3. ✅ Proper Relationships

**User → BenchmarkResult**: One-to-many
- Users can create multiple benchmark results
- Cascade delete: removing user removes their results

**User → BenchmarkSweep**: One-to-many
- Users can create multiple sweeps
- Cascade delete: removing user removes their sweeps

**BenchmarkSweep → BenchmarkResult**: One-to-many
- A sweep contains multiple results
- Cascade delete: removing sweep removes its results
- Optional: results can exist without a sweep

### 4. ✅ Status Tracking

Reuses existing `JobStatus` enum:
```python
class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPLETED_WITH_ERRORS = "completed_with_errors"
```

**Benefits**:
- Consistent with existing experiments
- Enables progress tracking
- Supports async execution (future)

### 5. ✅ Performance Optimization

**Indexes for common queries**:
- By method: Find all results for a specific UQ method
- By user: Find all results for a user
- By sweep: Find all results in a sweep
- By status: Find running/failed sweeps

**Query examples**:
```python
# Find all Gaussian Logits results
results = session.exec(
    select(BenchmarkResult).where(BenchmarkResult.method == "gaussian_logits")
).all()

# Find user's sweeps
sweeps = session.exec(
    select(BenchmarkSweep).where(BenchmarkSweep.created_by_id == user_id)
).all()

# Find running sweeps
running = session.exec(
    select(BenchmarkSweep).where(BenchmarkSweep.status == JobStatus.RUNNING)
).all()
```

## Migration Instructions

### Option 1: Automatic (Recommended)
SQLModel will create tables automatically on backend startup:
```bash
cd uqlab-streamlit/backend
uvicorn app.main:app --reload
```

### Option 2: Manual Python Script
```bash
cd uqlab-streamlit
python3 backend/run_benchmark_migration.py
```

Output:
```
============================================================
UQ Benchmarks Database Migration
============================================================
📊 Connecting to database: backend/app.db
🔄 Running migration...
✅ Migration completed successfully!
✅ Verified: Created 2 tables
   - benchmarkresult
   - benchmarksweep
============================================================
```

### Option 3: Manual SQL
```bash
cd uqlab-streamlit/backend
sqlite3 app.db < migrations/add_benchmark_tables.sql
```

## Verification

### Check Tables Exist
```bash
sqlite3 backend/app.db "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'benchmark%';"
```

Expected output:
```
benchmarkresult
benchmarksweep
```

### Check Indexes
```bash
sqlite3 backend/app.db "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_benchmark%';"
```

Expected output:
```
idx_benchmarkresult_method
idx_benchmarkresult_created_by
idx_benchmarkresult_sweep
idx_benchmarksweep_method
idx_benchmarksweep_created_by
idx_benchmarksweep_status
```

## Usage Examples

### Store a Benchmark Result
```python
from app.tables import BenchmarkResult, JobStatus
import json
from datetime import datetime

# Create result
result = BenchmarkResult(
    method="gaussian_logits",
    framework="keras",
    dataset_config_json=json.dumps({
        "under_supported_classes": [3, 5],
        "under_train_per_class": 50,
        "regular_train_per_class": 300,
        "noise_rate": 0.2
    }),
    training_config_json=json.dumps({
        "epochs": 10,
        "batch_size": 32
    }),
    evaluation_config_json=json.dumps({
        "mc_passes": 20
    }),
    accuracy=0.85,
    aleatoric_uncertainty=0.15,
    epistemic_uncertainty=0.08,
    training_time=45.2,
    evaluation_time=12.3,
    status=JobStatus.COMPLETED,
    created_at=datetime.utcnow(),
    created_by_id=user.id
)

session.add(result)
session.commit()
```

### Create a Sweep
```python
from app.tables import BenchmarkSweep, JobStatus
import json

sweep = BenchmarkSweep(
    name="Label Noise Sweep",
    description="Test aleatoric uncertainty with varying noise",
    method="gaussian_logits",
    sweep_parameter="noise_rate",
    sweep_values_json=json.dumps([0.0, 0.1, 0.2, 0.3, 0.4]),
    base_config_json=json.dumps({
        "dataset_config": {
            "under_supported_classes": [3, 5],
            "under_train_per_class": 50,
            "regular_train_per_class": 300
        },
        "training_config": {
            "epochs": 10,
            "batch_size": 32
        }
    }),
    status=JobStatus.QUEUED,
    total_runs=5,
    completed_runs=0,
    failed_runs=0,
    created_at=datetime.utcnow(),
    created_by_id=user.id
)

session.add(sweep)
session.commit()
```

### Query Results
```python
from sqlmodel import select

# Get all results for a method
results = session.exec(
    select(BenchmarkResult)
    .where(BenchmarkResult.method == "gaussian_logits")
    .order_by(BenchmarkResult.created_at.desc())
).all()

# Get sweep with results
sweep = session.get(BenchmarkSweep, sweep_id)
sweep_results = session.exec(
    select(BenchmarkResult)
    .where(BenchmarkResult.sweep_id == sweep_id)
    .order_by(BenchmarkResult.created_at)
).all()

# Get user's benchmarks
user_results = session.exec(
    select(BenchmarkResult)
    .where(BenchmarkResult.created_by_id == user_id)
).all()
```

## Integration with Existing System

### Backward Compatibility ✅
- **Existing experiments**: Continue to work unchanged
- **Existing API endpoints**: No modifications needed
- **Existing Streamlit UI**: No changes required
- **Database migrations**: Additive only, no ALTER or DROP

### Forward Compatibility ✅
- **New endpoints**: Ready to use new tables (Phase 3)
- **Streamlit UI**: Can query and display benchmark results (Phase 5)
- **Visualization**: Can plot sweep results (Phase 6)

## Files Modified/Created

### Created:
1. **`backend/migrations/add_benchmark_tables.sql`** (85 lines)
   - SQL migration script
   - Creates tables and indexes
   - SQLite compatible

2. **`backend/run_benchmark_migration.py`** (67 lines)
   - Python migration runner
   - Verification and error handling

3. **`PHASE4_DATABASE_SCHEMA.md`** (this file)
   - Comprehensive documentation

### Modified:
1. **`backend/app/tables.py`**
   - Added `BenchmarkResult` table (50 lines)
   - Added `BenchmarkSweep` table (40 lines)
   - Updated `User` model (2 new relationships)

2. **`backend/app/api/routes/uq_benchmarks.py`**
   - Added imports for new tables

3. **`backend/migrations/README.md`**
   - Documented new migration

## Next Steps (Phase 5)

### Streamlit UI Integration
1. **Add UQ Method Selector**
   - Dropdown for method selection
   - Show available methods from API

2. **Add Benchmark Configuration UI**
   - Form for dataset config
   - Form for training config
   - Form for evaluation config

3. **Add Results Display**
   - Table of benchmark results
   - Sweep progress tracking
   - Result comparison

4. **Add Sweep Configuration**
   - Parameter selector
   - Value range input
   - Preview of sweep runs

## Summary

✅ **Phase 4 Complete**: Database schema is production-ready

**Key Achievements**:
- 2 new tables with proper relationships
- 6 indexes for query optimization
- Complete migration scripts
- Zero breaking changes to existing system
- Full backward compatibility
- Ready for Phase 5 (Streamlit UI)

**Total Code**: ~250 lines of database schema + migrations

**Database Design Principles**:
- ✅ Additive only (no ALTER/DROP)
- ✅ Proper foreign keys and cascades
- ✅ Indexed for performance
- ✅ JSON for flexibility
- ✅ Status tracking for async execution
- ✅ Complete audit trail

**Next Phase**: Build Streamlit UI to interact with these tables