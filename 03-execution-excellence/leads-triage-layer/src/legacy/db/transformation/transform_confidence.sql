-- Populating staging.issue_predictions
TRUNCATE staging.issue_predictions;
INSERT INTO staging.issue_predictions (
    lead_id, has_issues_pred, has_issues_prob, has_scope_issue_pred, has_scope_issue_prob, 
    has_time_issue_pred, has_time_issue_prob, has_cavity_issue_pred, has_cavity_issue_prob,
    has_temperature_issue_pred, has_temperature_issue_prob, meta
)
SELECT 
    lead_id, has_issues_pred, has_issues_prob, has_scope_issue_pred, has_scope_issue_prob, 
    has_time_issue_pred, has_time_issue_prob, has_cavity_issue_pred, has_cavity_issue_prob,
    has_temperature_issue_pred, has_temperature_issue_prob, meta
FROM ods.issue_predictions;

-- Populating staging.confidence_predictions
TRUNCATE staging.confidence_predictions;
INSERT INTO staging.confidence_predictions (
    lead_id, confidence_score_pred, confidence_score_prob_3, 
    confidence_score_prob_4, confidence_score_prob_5, meta
)
SELECT 
    lead_id, confidence_score_pred, confidence_score_prob_3, 
    confidence_score_prob_4, confidence_score_prob_5, meta
FROM ods.confidence_predictions;

-- Adding columns to marts.lead_insights if they don't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='marts' AND table_name='lead_insights' AND column_name='has_issues_prob') THEN
        ALTER TABLE marts.lead_insights ADD COLUMN has_issues_prob DOUBLE PRECISION;
        ALTER TABLE marts.lead_insights ADD COLUMN has_issues_pred BIGINT;
        ALTER TABLE marts.lead_insights ADD COLUMN issue_meta TEXT;
        ALTER TABLE marts.lead_insights ADD COLUMN confidence_score_pred INTEGER;
        ALTER TABLE marts.lead_insights ADD COLUMN confidence_meta TEXT;
    END IF;
END $$;

-- Update marts.lead_insights with predictions from staging
UPDATE marts.lead_insights l
SET 
    has_issues_prob = i.has_issues_prob,
    has_issues_pred = i.has_issues_pred,
    issue_meta = i.meta,
    confidence_score_pred = c.confidence_score_pred,
    confidence_meta = c.meta
FROM staging.issue_predictions i
JOIN staging.confidence_predictions c ON i.lead_id = c.lead_id
WHERE l.lead_id = i.lead_id;

-- Adding columns to marts.project_insights if they don't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='marts' AND table_name='project_insights' AND column_name='confidence_score') THEN
        ALTER TABLE marts.project_insights ADD COLUMN confidence_score INTEGER;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='marts' AND table_name='project_insights' AND column_name='has_issues_prob') THEN
        ALTER TABLE marts.project_insights ADD COLUMN has_issues_prob DOUBLE PRECISION;
        ALTER TABLE marts.project_insights ADD COLUMN confidence_score_pred INTEGER;
    END IF;
END $$;

-- (Confidence Score is now calculated via Python script: src/db/transformation/calculate_confidence_labels.py)
-- This allows for more complex logic and handling of NULL satisfaction scores.

-- Update marts.project_insights with training results
UPDATE marts.project_insights p
SET 
    has_issues_prob = tr_i.has_issues_prob,
    confidence_score_pred = tr_c.confidence_score_pred
FROM prediction.issue_training_results tr_i
JOIN prediction.confidence_training_results tr_c ON tr_i.project_id = tr_c.project_id
WHERE p.project_id = tr_i.project_id;

-- Ensure N/A cases (-1) also show -1 in the prediction column
UPDATE marts.project_insights
SET confidence_score_pred = -1
WHERE confidence_score = -1;

-- Create confidence_training_data view for ML
CREATE OR REPLACE VIEW marts.confidence_training_data AS
SELECT 
    p.project_id,
    p.region,
    p.product,
    p.customer_segment,
    p.call_duration_min,
    p.building_year,
    p.has_hohlraum,
    p.heating_system,
    p.has_issues_prob,
    p.confidence_score
FROM marts.project_insights p
WHERE p.confidence_score > 0;
