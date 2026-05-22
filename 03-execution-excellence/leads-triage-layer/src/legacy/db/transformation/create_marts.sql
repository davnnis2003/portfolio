-- Create project_insights mart table
-- This table provides a curated view of past projects with calculated metrics and flattened flags.
DROP TABLE IF EXISTS marts.project_insights CASCADE;

CREATE TABLE marts.project_insights AS
SELECT
    *,
    COALESCE(final_quote_eur, 0) - COALESCE(initial_quote_eur, 0) AS quote_variance,
    jsonb_array_length (on_site_issues) AS num_issues,
    (jsonb_array_length (on_site_issues) >= 1) AS has_issues,
    EXISTS (
        SELECT
            1
        FROM
            jsonb_array_elements (on_site_issues) AS e
        WHERE
            e ->> 'category' = 'scope_estimate_off'
    ) AS has_scope_issue,
    EXISTS (
        SELECT
            1
        FROM
            jsonb_array_elements (on_site_issues) AS e
        WHERE
            e ->> 'category' = 'time_too_short'
    ) AS has_time_issue,
    EXISTS (
        SELECT
            1
        FROM
            jsonb_array_elements (on_site_issues) AS e
        WHERE
            e ->> 'category' = 'cavity_size_off'
    ) AS has_cavity_issue,
    EXISTS (
        SELECT
            1
        FROM
            jsonb_array_elements (on_site_issues) AS e
        WHERE
            e ->> 'category' = 'temperature_too_low'
    ) AS has_temperature_issue,
    (completed_at - created_at) AS project_duration_days,
    NULL::TEXT AS triage_labels,
    NULL::INTEGER AS confidence_score,
    NULL::DOUBLE PRECISION AS has_issues_prob,
    NULL::INTEGER AS confidence_score_pred
FROM
    staging.past_projects;

-- Add comments for documentation
COMMENT ON TABLE marts.project_insights IS 'Curated project data for analysis, including issue flags and pricing variance.';

COMMENT ON COLUMN marts.project_insights.quote_variance IS 'Difference between final and initial quote.';

COMMENT ON COLUMN marts.project_insights.num_issues IS 'Total number of on-site issues recorded.';

COMMENT ON COLUMN marts.project_insights.has_scope_issue IS 'True if the project had a scope estimation issue.';

COMMENT ON COLUMN marts.project_insights.has_time_issue IS 'True if the project had a timing/scheduling issue.';

COMMENT ON COLUMN marts.project_insights.has_cavity_issue IS 'True if the cavity size was different than planned.';

COMMENT ON COLUMN marts.project_insights.has_temperature_issue IS 'True if the temperature was too low for installation.';

-- Create lead_insights mart table
DROP TABLE IF EXISTS marts.lead_insights CASCADE;

CREATE TABLE marts.lead_insights AS
SELECT
    l.lead_id,
    l.created_at,
    l.customer_segment,
    l.region,
    l.product,
    l.call_duration_min,
    (l.call_duration_min > 10) AS is_high_duration_call,
    l.building_year,
    (2026 - l.building_year) AS building_age,
    (l.building_year < 1980) AS is_old_building,
    l.has_hohlraum,
    l.heating_system,
    l.n_vollgeschosse,
    l.fassaden_typ,
    l.mauerstarke_cm,
    l.is_gewoelbekeller,
    l.feuchtigkeit,
    l.dachboden_zukunft_wohnraum,
    t.transcript_text,
    t.word_count,
    NULL::TEXT AS triage_decision,
    NULL::DOUBLE PRECISION AS has_issues_prob,
    NULL::BIGINT AS has_issues_pred,
    NULL::TEXT AS issue_meta,
    NULL::INTEGER AS confidence_score_pred,
    NULL::TEXT AS confidence_meta
FROM
    staging.new_leads l
LEFT JOIN
    staging.new_lead_transcripts t ON l.lead_id = t.lead_id;

-- Add comments for documentation
COMMENT ON TABLE marts.lead_insights IS 'Curated lead data for analysis and triage prioritization, including full transcripts.';

COMMENT ON COLUMN marts.lead_insights.is_high_duration_call IS 'True if the qualification call lasted more than 10 minutes.';

COMMENT ON COLUMN marts.lead_insights.building_age IS 'Calculated age of the building as of 2026.';

COMMENT ON COLUMN marts.lead_insights.is_old_building IS 'True if the building was built before 1980 (higher insulation potential).';

COMMENT ON COLUMN marts.lead_insights.transcript_text IS 'Full text of the qualification call transcript.';

COMMENT ON COLUMN marts.lead_insights.word_count IS 'Total word count of the transcript.';