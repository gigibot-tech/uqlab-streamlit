-- Migration: Add UQ Benchmarks tables
-- Phase 4: Database schema for new uq_benchmarks package
-- SQLite compatible version

-- Table: benchmarkresult
-- Stores individual benchmark experiment results
CREATE TABLE IF NOT EXISTS benchmarkresult (
    id TEXT PRIMARY KEY,
    method TEXT NOT NULL,
    framework TEXT NOT NULL,
    dataset_config_json TEXT NOT NULL,
    training_config_json TEXT NOT NULL,
    evaluation_config_json TEXT NOT NULL,
    accuracy REAL NOT NULL,
    aleatoric_uncertainty REAL NOT NULL,
    epistemic_uncertainty REAL NOT NULL,
    training_time REAL NOT NULL,
    evaluation_time REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed',
    error_message TEXT,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    created_by_id TEXT NOT NULL,
    sweep_id TEXT,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (sweep_id) REFERENCES benchmarksweep(id) ON DELETE CASCADE
);

-- Index for faster queries by method
CREATE INDEX IF NOT EXISTS idx_benchmarkresult_method ON benchmarkresult(method);

-- Index for faster queries by user
CREATE INDEX IF NOT EXISTS idx_benchmarkresult_created_by ON benchmarkresult(created_by_id);

-- Index for faster queries by sweep
CREATE INDEX IF NOT EXISTS idx_benchmarkresult_sweep ON benchmarkresult(sweep_id);


-- Table: benchmarksweep
-- Stores parameter sweep configurations and aggregate status
CREATE TABLE IF NOT EXISTS benchmarksweep (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    method TEXT NOT NULL,
    sweep_parameter TEXT NOT NULL,
    sweep_values_json TEXT NOT NULL,
    base_config_json TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    progress REAL NOT NULL DEFAULT 0.0,
    total_runs INTEGER NOT NULL DEFAULT 0,
    completed_runs INTEGER NOT NULL DEFAULT 0,
    failed_runs INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    created_by_id TEXT NOT NULL,
    FOREIGN KEY (created_by_id) REFERENCES user(id) ON DELETE CASCADE
);

-- Index for faster queries by method
CREATE INDEX IF NOT EXISTS idx_benchmarksweep_method ON benchmarksweep(method);

-- Index for faster queries by user
CREATE INDEX IF NOT EXISTS idx_benchmarksweep_created_by ON benchmarksweep(created_by_id);

-- Index for faster queries by status
CREATE INDEX IF NOT EXISTS idx_benchmarksweep_status ON benchmarksweep(status);


-- Note: SQLite doesn't support COMMENT ON COLUMN
-- Documentation:
-- 
-- benchmarkresult table:
--   - Stores results from individual UQ benchmark runs
--   - method: UQ method name (e.g., "gaussian_logits", "information_theoretic")
--   - framework: "keras" or "pytorch"
--   - *_config_json: JSON strings with full configuration
--   - accuracy, aleatoric_uncertainty, epistemic_uncertainty: Core metrics
--   - training_time, evaluation_time: Performance metrics in seconds
--   - sweep_id: Optional link to parent sweep experiment
--
-- benchmarksweep table:
--   - Stores parameter sweep experiments
--   - sweep_parameter: Name of parameter being swept (e.g., "noise_rate")
--   - sweep_values_json: JSON array of parameter values
--   - base_config_json: Configuration for non-swept parameters
--   - Aggregate status tracking (total_runs, completed_runs, failed_runs)

-- Made with Bob