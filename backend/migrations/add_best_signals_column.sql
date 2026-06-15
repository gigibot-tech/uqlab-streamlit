-- Migration: Add best_signals_json column to uncertaintyexperiment table
-- This stores the complete 7-signal AUROC data as JSON
-- SQLite compatible version

ALTER TABLE uncertaintyexperiment
ADD COLUMN best_signals_json TEXT DEFAULT NULL;

-- Note: SQLite doesn't support COMMENT ON COLUMN
-- Documentation: This column stores JSON with all 7 uncertainty signals

-- Made with Bob
