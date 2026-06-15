-- Migration: Add method_type column to batchexperiment table
-- Date: 2026-05-26
-- Description: Adds method_type column to support attribution vs benchmark batch experiments

-- Add method_type column as nullable (optional for backward compatibility)
ALTER TABLE batchexperiment
ADD COLUMN method_type VARCHAR(50);

-- Optionally update existing rows to have 'attribution' if desired
-- UPDATE batchexperiment
-- SET method_type = 'attribution'
-- WHERE method_type IS NULL;

-- Made with Bob