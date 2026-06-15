# Database Migrations

## Migration 1: Add best_signals_json Column

**File**: `add_best_signals_column.sql`

**Purpose**: Add a TEXT column to store all 7 uncertainty signals as JSON.

**Signals Stored**:
1. msp_uncertainty
2. predictive_entropy
3. mutual_info
4. inverse_coherence (aleatoric indicator)
5. dominance (epistemic indicator)
6. inverse_mass (best epistemic, 0.94 AUROC)
7. inverse_logit_magnitude

**How to Run**:

### Option 1: Using the migration script
```bash
cd walaris-cen
python3 backend/run_migration.py
```

### Option 2: Manual SQL execution
Connect to your PostgreSQL database and run:
```sql
ALTER TABLE uncertaintyexperiment
ADD COLUMN IF NOT EXISTS best_signals_json TEXT DEFAULT NULL;
```

### Option 3: Automatic on backend startup
The backend will automatically create the column if it doesn't exist when SQLModel creates tables.

**Data Structure**:
```json
{
  "one_vs_rest_auroc": [
    {
      "signal": "msp_uncertainty",
      "aleatoric_like_auroc": 0.65,
      "epistemic_like_auroc": 0.72
    },
    ...
  ]
}
```

**Backward Compatibility**:
- Existing experiments will have `best_signals_json = NULL`
- New experiments will populate this field automatically
- The old `aleatoric_auroc` and `epistemic_auroc` fields remain for backward compatibility

---

## Migration 2: Add UQ Benchmarks Tables (Phase 4)

**File**: `add_benchmark_tables.sql`

**Purpose**: Create new tables for storing UQ benchmark experiment results from the `uq_benchmarks` package.

**Tables Created**:

### 1. `benchmarkresult`
Stores individual benchmark experiment results.

**Columns**:
- `id`: Primary key (UUID)
- `method`: UQ method name (e.g., "gaussian_logits", "information_theoretic")
- `framework`: Framework used ("keras" or "pytorch")
- `dataset_config_json`: Dataset configuration as JSON
- `training_config_json`: Training hyperparameters as JSON
- `evaluation_config_json`: Evaluation settings as JSON
- `accuracy`: Model accuracy (0-1)
- `aleatoric_uncertainty`: Aleatoric uncertainty score
- `epistemic_uncertainty`: Epistemic uncertainty score
- `training_time`: Training duration in seconds
- `evaluation_time`: Evaluation duration in seconds
- `status`: Job status (queued, running, completed, failed)
- `error_message`: Error details if failed
- `created_at`, `started_at`, `completed_at`: Timestamps
- `created_by_id`: Foreign key to user table
- `sweep_id`: Optional foreign key to benchmarksweep table

**Indexes**:
- `idx_benchmarkresult_method`: Fast queries by method
- `idx_benchmarkresult_created_by`: Fast queries by user
- `idx_benchmarkresult_sweep`: Fast queries by sweep

### 2. `benchmarksweep`
Stores parameter sweep experiments.

**Columns**:
- `id`: Primary key (UUID)
- `name`: Sweep name
- `description`: Optional description
- `method`: UQ method being swept
- `sweep_parameter`: Parameter name (e.g., "noise_rate", "under_train_per_class")
- `sweep_values_json`: JSON array of parameter values
- `base_config_json`: Configuration for non-swept parameters
- `status`: Aggregate status
- `progress`: Progress percentage (0-100)
- `total_runs`, `completed_runs`, `failed_runs`: Run counters
- `created_at`, `started_at`, `completed_at`: Timestamps
- `created_by_id`: Foreign key to user table

**Indexes**:
- `idx_benchmarksweep_method`: Fast queries by method
- `idx_benchmarksweep_created_by`: Fast queries by user
- `idx_benchmarksweep_status`: Fast queries by status

**How to Run**:

### Option 1: Using the migration script
```bash
cd walaris-cen
python3 backend/run_benchmark_migration.py
```

### Option 2: Manual SQL execution
```bash
cd walaris-cen/backend
sqlite3 app.db < migrations/add_benchmark_tables.sql
```

### Option 3: Automatic on backend startup
SQLModel will automatically create these tables when the backend starts if they don't exist.

**Backward Compatibility**:
- ✅ **Additive only**: No changes to existing tables
- ✅ **No data migration needed**: New tables start empty
- ✅ **Existing experiments unaffected**: Old experiments continue to work
- ✅ **User relationships preserved**: Links to existing user table

**Usage Example**:
```python
from app.tables import BenchmarkResult, BenchmarkSweep

# Create a benchmark result
result = BenchmarkResult(
    method="gaussian_logits",
    framework="keras",
    dataset_config_json='{"noise_rate": 0.2}',
    training_config_json='{"epochs": 10}',
    evaluation_config_json='{"mc_passes": 20}',
    accuracy=0.85,
    aleatoric_uncertainty=0.15,
    epistemic_uncertainty=0.08,
    training_time=45.2,
    evaluation_time=12.3,
    created_by_id=user_id
)
session.add(result)
session.commit()
```

**Integration with FastAPI**:
- New endpoints at `/api/v1/uq-benchmarks/*`
- Results automatically stored in these tables
- Query results by method, user, or sweep