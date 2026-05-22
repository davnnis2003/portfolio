import json
import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database connection parameters
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "climatetech_triage"),
    "user": os.getenv("DB_USER", "climatetech_admin"),
    "password": os.getenv("DB_PASSWORD", "climatetech_password"),
    "port": int(os.getenv("DB_PORT", 5432))
}

def get_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        # Set search_path to include our new schemas
        cursor = conn.cursor()
        cursor.execute("SET search_path TO ods, staging, marts, feature_store")
        cursor.close()
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def load_past_projects(conn, file_path):
    print(f"Loading past projects from {file_path}...")
    projects = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                data = json.loads(line)
                projects.append((
                    data.get("project_id"),
                    data.get("created_at"),
                    json.dumps(data)
                ))
        
        cursor = conn.cursor()
        query = "INSERT INTO ods.past_projects (project_id, created_at, data) VALUES %s ON CONFLICT (project_id) DO UPDATE SET data = EXCLUDED.data"
        execute_values(cursor, query, projects)
        conn.commit()
        print(f"Successfully loaded {len(projects)} projects.")
    except Exception as e:
        print(f"Error loading projects: {e}")

def load_new_leads(conn, leads_dir):
    print(f"Loading new leads from {leads_dir}...")
    leads_count = 0
    try:
        for lead_id in os.listdir(leads_dir):
            lead_path = os.path.join(leads_dir, lead_id)
            if not os.path.isdir(lead_path):
                continue
            
            intake_file = os.path.join(lead_path, "intake.json")
            transcript_file = os.path.join(lead_path, "transcript.md")
            
            if not os.path.exists(intake_file):
                print(f"Warning: No intake.json found in {lead_id}")
                continue
            
            with open(intake_file, 'r') as f:
                intake_data = json.load(f)
            
            transcript_text = ""
            if os.path.exists(transcript_file):
                with open(transcript_file, 'r') as f:
                    transcript_text = f.read()
            
            cursor = conn.cursor()
            query = """
                INSERT INTO ods.new_leads (lead_id, created_at, intake_data, transcript_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (lead_id) DO UPDATE 
                SET intake_data = EXCLUDED.intake_data, 
                    transcript_text = EXCLUDED.transcript_text
            """
            cursor.execute(query, (
                intake_data.get("lead_id"),
                intake_data.get("created_at"),
                json.dumps(intake_data),
                transcript_text
            ))

            # Ingest into dedicated transcript table
            if transcript_text:
                transcript_query = """
                    INSERT INTO ods.new_lead_transcripts (lead_id, transcript_text, filename)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (lead_id) DO UPDATE 
                    SET transcript_text = EXCLUDED.transcript_text,
                        filename = EXCLUDED.filename,
                        ingested_at = CURRENT_TIMESTAMP
                """
                cursor.execute(transcript_query, (
                    intake_data.get("lead_id"),
                    transcript_text,
                    "transcript.md"
                ))
            
            leads_count += 1
        
        conn.commit()
        print(f"Successfully loaded {leads_count} leads.")
    except Exception as e:
        print(f"Error loading leads: {e}")

if __name__ == "__main__":
    conn = get_connection()
    if conn:
        load_past_projects(conn, "data/past_projects.jsonl")
        load_new_leads(conn, "data/new_leads")
        conn.close()
