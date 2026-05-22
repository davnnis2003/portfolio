-- Refactor database schemas
-- 1. Rename public to ods
ALTER SCHEMA public RENAME TO ods;

-- 2. Create other schemas
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS feature_store;

-- 3. Move past_projects_parsed to staging
ALTER TABLE ods.past_projects_parsed SET SCHEMA staging;

-- 4. Update search path for the user to maintain compatibility
ALTER ROLE climatetech_admin SET search_path TO ods, staging, marts, feature_store;
