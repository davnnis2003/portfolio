import os
import pandas as pd
import numpy as np
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

def calculate_confidence(row):
    stage = row['stage']
    
    # 1. Base Score by Project Stage (Proxy for Lead Quality)
    if stage == 'signed_installed':
        score = 4.0
    elif stage == 'qualified_lost':
        score = 3.0
    elif stage == 'qualified_declined':
        score = 2.5
    elif stage == 'disqualified_phase1':
        score = 1.0
    else:
        score = 0.0
    
    # 2. Satisfaction Modifier (only for installed projects)
    sat = row['customer_satisfaction']
    if pd.notnull(sat) and stage == 'signed_installed':
        if sat >= 5:
            score += 1.0
        elif sat >= 4:
            score += 0.5
        elif sat == 3:
            score -= 0.5
        else:
            score -= 1.5
    
    # 3. Issues Modifier
    num_issues = row['num_issues'] or 0
    if stage == 'signed_installed':
        if num_issues == 0:
            score += 0.5
        elif num_issues == 1:
            score -= 0.5
        else:
            score -= 1.5
    elif num_issues > 0: # Issues identified even if not installed
        score -= 1.0
        
    # 4. Quote Variance Modifier
    var = row['quote_variance']
    if pd.notnull(var):
        if abs(var) < 0.03:
            score += 0.5
        elif abs(var) > 0.10:
            score -= 0.5
            
    # 5. Technical Risk: Moisture
    if row['feuchtigkeit'] is True:
        score -= 1.0
        
    # 6. Engagement Proxy: Call Duration
    duration = row['call_duration_min']
    if pd.notnull(duration):
        if duration > 15:
            score += 0.3
        elif duration < 7:
            score -= 0.3
            
    # Final clamping and rounding
    # Resulting distribution will be -1 (N/A) or 1-5
    final_score = int(round(score))
    if final_score <= 0:
        return -1
    return int(max(1, min(5, final_score)))

def main():
    print("Fetching project data for confidence score calculation...")
    query = "SELECT * FROM marts.project_insights"
    df = pd.read_sql(query, engine)
    
    print(f"Processing {len(df)} projects...")
    df['confidence_score'] = df.apply(calculate_confidence, axis=1)
    
    # Check distribution
    print("\nNew Confidence Score distribution:")
    print(df['confidence_score'].value_counts().sort_index())
    
    print("\nUpdating database...")
    # We only need project_id and the new score
    df_update = df[['project_id', 'confidence_score']]
    
    # Use a temporary table for bulk update
    df_update.to_sql('tmp_confidence_update', engine, if_exists='replace', index=False)
    
    update_query = """
    UPDATE marts.project_insights p
    SET confidence_score = t.confidence_score
    FROM tmp_confidence_update t
    WHERE p.project_id = t.project_id;
    
    DROP TABLE tmp_confidence_update;
    """
    
    with engine.connect() as conn:
        conn.execute(text(update_query))
        conn.commit()
    
    print("Database update completed.")

if __name__ == "__main__":
    main()
