-- Populating staging.triage_predictions
TRUNCATE staging.triage_predictions;
INSERT INTO staging.triage_predictions (
    lead_id, triage_decision_pred, pitch_prob, 
    pitch_with_flag_prob, pitch_with_cross_sell_prob, disqualify_prob, escalate_prob, meta
)
SELECT 
    lead_id, triage_decision_pred, pitch_prob, 
    pitch_with_flag_prob, pitch_with_cross_sell_prob, disqualify_prob, escalate_prob, meta
FROM ods.triage_predictions;

-- Update marts.lead_insights with triage predictions
UPDATE marts.lead_insights l
SET 
    triage_decision = t.triage_decision_pred
FROM staging.triage_predictions t
WHERE l.lead_id = t.lead_id;

-- Update marts.project_insights with training results
UPDATE marts.project_insights p
SET 
    triage_labels = tr.triage_labels
FROM prediction.triage_training_results tr
WHERE p.project_id = tr.project_id;
