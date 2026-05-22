import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DB_USER = os.getenv("DB_USER", "climatetech_admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "climatetech_password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "climatetech_triage")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

def ingest_predictions():
    print("Ingesting predictions from prediction.issue_predictions to ods.issue_predictions...")
    
    ingest_query = """
    INSERT INTO ods.issue_predictions (
        lead_id, has_issues_pred, has_issues_prob, 
        has_scope_issue_pred, has_scope_issue_prob,
        has_time_issue_pred, has_time_issue_prob,
        has_cavity_issue_pred, has_cavity_issue_prob,
        has_temperature_issue_pred, has_temperature_issue_prob,
        meta
    )
    SELECT 
        lead_id, has_issues_pred, has_issues_prob, 
        has_scope_issue_pred, has_scope_issue_prob,
        has_time_issue_pred, has_time_issue_prob,
        has_cavity_issue_pred, has_cavity_issue_prob,
        has_temperature_issue_pred, has_temperature_issue_prob,
        meta
    FROM prediction.issue_predictions
    ON CONFLICT (lead_id) DO UPDATE SET
        has_issues_pred = EXCLUDED.has_issues_pred,
        has_issues_prob = EXCLUDED.has_issues_prob,
        has_scope_issue_pred = EXCLUDED.has_scope_issue_pred,
        has_scope_issue_prob = EXCLUDED.has_scope_issue_prob,
        has_time_issue_pred = EXCLUDED.has_time_issue_pred,
        has_time_issue_prob = EXCLUDED.has_time_issue_prob,
        has_cavity_issue_pred = EXCLUDED.has_cavity_issue_pred,
        has_cavity_issue_prob = EXCLUDED.has_cavity_issue_prob,
        has_temperature_issue_pred = EXCLUDED.has_temperature_issue_pred,
        has_temperature_issue_prob = EXCLUDED.has_temperature_issue_prob,
        meta = EXCLUDED.meta,
        ingested_at = CURRENT_TIMESTAMP;
    """
    
    with engine.connect() as conn:
        conn.execute(text(ingest_query))
        conn.commit()
    
    print("Ingestion for issues completed.")

    print("Ingesting predictions from prediction.confidence_predictions to ods.confidence_predictions...")
    conf_ingest_query = """
    INSERT INTO ods.confidence_predictions (
        lead_id, confidence_score_pred, 
        confidence_score_prob_3, confidence_score_prob_4, confidence_score_prob_5,
        meta
    )
    SELECT 
        lead_id, confidence_score_pred, 
        confidence_score_prob_3, confidence_score_prob_4, confidence_score_prob_5,
        meta
    FROM prediction.confidence_predictions
    ON CONFLICT (lead_id) DO UPDATE SET
        confidence_score_pred = EXCLUDED.confidence_score_pred,
        confidence_score_prob_3 = EXCLUDED.confidence_score_prob_3,
        confidence_score_prob_4 = EXCLUDED.confidence_score_prob_4,
        confidence_score_prob_5 = EXCLUDED.confidence_score_prob_5,
        meta = EXCLUDED.meta,
        ingested_at = CURRENT_TIMESTAMP;
    """
    
    with engine.connect() as conn:
        conn.execute(text(conf_ingest_query))
        conn.commit()
    
    print("Ingestion for confidence completed.")

    print("Ingesting predictions from prediction.triage_predictions to ods.triage_predictions...")
    triage_ingest_query = """
    INSERT INTO ods.triage_predictions (
        lead_id, triage_decision_pred, 
        pitch_prob, pitch_with_flag_prob, pitch_with_cross_sell_prob, disqualify_prob, escalate_prob,
        meta
    )
    SELECT 
        lead_id, triage_decision_pred, 
        pitch_prob, pitch_with_flag_prob, pitch_with_cross_sell_prob, disqualify_prob, escalate_prob,
        meta
    FROM prediction.triage_predictions
    ON CONFLICT (lead_id) DO UPDATE SET
        triage_decision_pred = EXCLUDED.triage_decision_pred,
        pitch_prob = EXCLUDED.pitch_prob,
        pitch_with_flag_prob = EXCLUDED.pitch_with_flag_prob,
        pitch_with_cross_sell_prob = EXCLUDED.pitch_with_cross_sell_prob,
        disqualify_prob = EXCLUDED.disqualify_prob,
        escalate_prob = EXCLUDED.escalate_prob,
        meta = EXCLUDED.meta,
        ingested_at = CURRENT_TIMESTAMP;
    """
    
    with engine.connect() as conn:
        conn.execute(text(triage_ingest_query))
        conn.commit()
    
    print("Ingestion for triage completed.")

if __name__ == "__main__":
    ingest_predictions()
