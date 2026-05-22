import os
import pandas as pd
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

CROSS_SELL_KEYWORDS = [
    "zusätzlich", "weitere produkte", "solar", "wärmepumpe", 
    "fenster", "dach", "keller", "cross sell", "cross-sell",
    "pv-anlage", "photovoltaik", "heizungstausch"
]

def calculate_triage_label(row):
    stage = row['stage']
    has_issues = row['has_issues']
    summary = (row['sales_call_summary'] or "").lower()
    
    # 1. Escalate: Complex cases requiring human review
    escalate_keywords = [
        'uncertain', 'complex', 'manual review', 'specialist needed', 'unclear',
        'komplex', 'unklar', 'prüfen', 'manuell', 'schwierig', 'edge case',
        'sonderfall', 'abklären', 'unsicher'
    ]
    if any(kw in summary for kw in escalate_keywords):
        return 'escalate'

    # 2. Disqualify
    if stage == 'disqualified_phase1':
        return 'disqualify'
    
    # 3. Pitch with Flag (if issues occurred)
    if has_issues:
        return 'pitch_with_flag'
    
    # 4. Pitch with Cross-Sell
    for kw in CROSS_SELL_KEYWORDS:
        if kw in summary:
            return 'pitch_with_cross_sell'
    
    # 5. Default Pitch
    return 'pitch'

def main():
    print("Fetching project data for triage label calculation...")
    query = "SELECT project_id, stage, has_issues, sales_call_summary FROM marts.project_insights"
    df = pd.read_sql(query, engine)
    
    print(f"Processing {len(df)} projects...")
    df['triage_labels'] = df.apply(calculate_triage_label, axis=1)
    
    # Check distribution
    print("\nNew Triage Label distribution:")
    print(df['triage_labels'].value_counts())
    
    print("\nUpdating database...")
    # Use a temporary table for bulk update
    df_update = df[['project_id', 'triage_labels']]
    df_update.to_sql('tmp_triage_update', engine, if_exists='replace', index=False)
    
    update_query = """
    UPDATE marts.project_insights p
    SET triage_labels = t.triage_labels
    FROM tmp_triage_update t
    WHERE p.project_id = t.project_id;
    
    DROP TABLE tmp_triage_update;
    """
    
    with engine.connect() as conn:
        conn.execute(text(update_query))
        conn.commit()
    
    print("Database update completed.")

if __name__ == "__main__":
    main()
