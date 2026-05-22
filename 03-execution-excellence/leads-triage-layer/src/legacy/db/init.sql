-- Schema for ClimateTech Case Study Triage Layer

-- Create schemas
CREATE SCHEMA IF NOT EXISTS ods;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS marts;
CREATE SCHEMA IF NOT EXISTS feature_store;

-- Set default search path
SET search_path TO ods, staging, marts, feature_store;

-- ODS: First landing schema
CREATE TABLE IF NOT EXISTS ods.past_projects (
    id SERIAL PRIMARY KEY,
    project_id TEXT UNIQUE NOT NULL,
    created_at DATE,
    data JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS ods.new_leads (
    id SERIAL PRIMARY KEY,
    lead_id TEXT UNIQUE NOT NULL,
    created_at DATE,
    intake_data JSONB NOT NULL,
    transcript_text TEXT,
    status TEXT DEFAULT 'pending', -- pending, processed, escalated
    decision TEXT, -- pitch, disqualify, escalate, pitch_with_flag, pitch_with_cross_sell
    confidence_score INTEGER, -- 1-5
    reasoning TEXT
);

CREATE TABLE IF NOT EXISTS ods.new_lead_transcripts (
    lead_id TEXT PRIMARY KEY,
    transcript_text TEXT NOT NULL,
    filename TEXT,
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.issue_predictions (
    lead_id TEXT PRIMARY KEY,
    has_issues_pred BIGINT,
    has_issues_prob DOUBLE PRECISION,
    has_scope_issue_pred BIGINT,
    has_scope_issue_prob DOUBLE PRECISION,
    has_time_issue_pred BIGINT,
    has_time_issue_prob DOUBLE PRECISION,
    has_cavity_issue_pred BIGINT,
    has_cavity_issue_prob DOUBLE PRECISION,
    has_temperature_issue_pred BIGINT,
    has_temperature_issue_prob DOUBLE PRECISION,
    meta TEXT, -- explainability
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.confidence_predictions (
    lead_id TEXT PRIMARY KEY,
    confidence_score_pred INTEGER,
    confidence_score_prob_3 DOUBLE PRECISION,
    confidence_score_prob_4 DOUBLE PRECISION,
    confidence_score_prob_5 DOUBLE PRECISION,
    meta TEXT, -- explainability
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods.triage_predictions (
    lead_id TEXT PRIMARY KEY,
    triage_decision_pred TEXT,
    pitch_prob DOUBLE PRECISION,
    pitch_with_flag_prob DOUBLE PRECISION,
    pitch_with_cross_sell_prob DOUBLE PRECISION,
    disqualify_prob DOUBLE PRECISION,
    escalate_prob DOUBLE PRECISION,
    meta TEXT, -- explainability
    ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_past_projects_data ON ods.past_projects USING GIN (data);
CREATE INDEX IF NOT EXISTS idx_new_leads_intake_data ON ods.new_leads USING GIN (intake_data);

-- STAGING: Basic transformed data
CREATE TABLE IF NOT EXISTS staging.past_projects (
    project_id TEXT PRIMARY KEY,
    created_at DATE,
    completed_at DATE,
    region TEXT,
    product TEXT,
    building_type TEXT,
    n_vollgeschosse INTEGER,
    building_year INTEGER,
    fassaden_typ TEXT,
    mauerstarke_cm NUMERIC,
    has_hohlraum BOOLEAN,
    hohlraum_size_cm NUMERIC,
    dachboden_genutzt_als TEXT,
    dachboden_zukunft_wohnraum BOOLEAN,
    existing_insulation BOOLEAN,
    is_gewoelbekeller BOOLEAN,
    feuchtigkeit BOOLEAN,
    customer_segment TEXT,
    customer_title TEXT,
    customer_surname TEXT,
    lead_source TEXT,
    heating_system TEXT,
    rep_id TEXT,
    call_duration_min INTEGER,
    sales_call_summary TEXT,
    sonderfaktor TEXT,
    nachbar_project_id TEXT,
    stage TEXT,
    disqualification_reason TEXT,
    initial_quote_eur NUMERIC,
    final_quote_eur NUMERIC,
    subsidy_program TEXT,
    subsidy_eligible BOOLEAN,
    installation_date DATE,
    on_site_issues JSONB,
    post_install_notes TEXT,
    customer_satisfaction INTEGER
);

-- STAGING: New Leads
CREATE TABLE IF NOT EXISTS staging.new_leads (
    lead_id TEXT PRIMARY KEY,
    created_at DATE,
    customer_title TEXT,
    customer_surname TEXT,
    customer_segment TEXT,
    region TEXT,
    postal_area TEXT,
    city TEXT,
    product TEXT,
    rep_id TEXT,
    call_duration_min INTEGER,
    building_type TEXT,
    building_year INTEGER,
    n_vollgeschosse INTEGER,
    heating_system TEXT,
    fassaden_typ TEXT,
    mauerstarke_cm NUMERIC,
    has_hohlraum BOOLEAN,
    hohlraum_size_cm NUMERIC,
    is_gewoelbekeller BOOLEAN,
    feuchtigkeit BOOLEAN,
    dachboden_zukunft_wohnraum BOOLEAN
);

-- STAGING: New Lead Transcripts
CREATE TABLE IF NOT EXISTS staging.new_lead_transcripts (
    lead_id TEXT PRIMARY KEY,
    transcript_text TEXT NOT NULL,
    word_count INTEGER,
    filename TEXT
);

CREATE TABLE IF NOT EXISTS staging.issue_predictions (
    lead_id TEXT PRIMARY KEY,
    has_issues_pred BIGINT,
    has_issues_prob DOUBLE PRECISION,
    has_scope_issue_pred BIGINT,
    has_scope_issue_prob DOUBLE PRECISION,
    has_time_issue_pred BIGINT,
    has_time_issue_prob DOUBLE PRECISION,
    has_cavity_issue_pred BIGINT,
    has_cavity_issue_prob DOUBLE PRECISION,
    has_temperature_issue_pred BIGINT,
    has_temperature_issue_prob DOUBLE PRECISION,
    meta TEXT
);

CREATE TABLE IF NOT EXISTS staging.confidence_predictions (
    lead_id TEXT PRIMARY KEY,
    confidence_score_pred INTEGER,
    confidence_score_prob_3 DOUBLE PRECISION,
    confidence_score_prob_4 DOUBLE PRECISION,
    confidence_score_prob_5 DOUBLE PRECISION,
    meta TEXT
);

CREATE TABLE IF NOT EXISTS staging.triage_predictions (
    lead_id TEXT PRIMARY KEY,
    triage_decision_pred TEXT,
    pitch_prob DOUBLE PRECISION,
    pitch_with_flag_prob DOUBLE PRECISION,
    pitch_with_cross_sell_prob DOUBLE PRECISION,
    disqualify_prob DOUBLE PRECISION,
    escalate_prob DOUBLE PRECISION,
    meta TEXT
);

-- MARTS: Curated data with business logic
CREATE TABLE IF NOT EXISTS marts.project_insights (
    project_id TEXT PRIMARY KEY,
    region TEXT,
    product TEXT,
    stage TEXT,
    initial_quote_eur NUMERIC,
    final_quote_eur NUMERIC,
    quote_variance NUMERIC,
    customer_satisfaction INTEGER,
    num_issues INTEGER,
    has_issues BOOLEAN,
    has_scope_issue BOOLEAN,
    has_time_issue BOOLEAN,
    has_cavity_issue BOOLEAN,
    has_temperature_issue BOOLEAN,
    project_duration_days INTEGER,
    triage_labels TEXT
);

-- MARTS: Lead Insights
CREATE TABLE IF NOT EXISTS marts.lead_insights (
    lead_id TEXT PRIMARY KEY,
    created_at DATE,
    customer_segment TEXT,
    region TEXT,
    product TEXT,
    call_duration_min INTEGER,
    is_high_duration_call BOOLEAN,
    building_year INTEGER,
    building_age INTEGER,
    is_old_building BOOLEAN,
    has_hohlraum BOOLEAN,
    heating_system TEXT,
    triage_decision TEXT
);

COMMENT ON TABLE marts.lead_insights IS 'Curated lead data for analysis and triage prioritization.';

COMMENT ON TABLE marts.project_insights IS 'Curated project data for analysis, including issue flags and pricing variance.';
