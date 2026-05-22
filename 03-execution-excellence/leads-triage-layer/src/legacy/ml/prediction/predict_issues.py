import os
import pandas as pd
import numpy as np
import joblib
import json
import shap
from sqlalchemy import create_engine, text, Text
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

MODEL_DIR = "src/ml/models/issues"

def set_primary_key(schema, table, column):
    print(f"Setting primary key {column} on {schema}.{table}...")
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {schema}.{table} ADD PRIMARY KEY ({column});"))
        conn.commit()

def load_leads():
    print("Loading lead data from database...")
    predict_query = """
    SELECT 
        lead_id, region, product, customer_segment, call_duration_min, 
        building_year, has_hohlraum, heating_system
    FROM marts.lead_insights
    """
    df_predict = pd.read_sql(predict_query, engine)
    return df_predict

def get_top_features(shap_values, feature_names, top_n=3):
    indices = np.argsort(np.abs(shap_values))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_values[i])} for i in indices]

def predict_and_save():
    df_predict = load_leads()
    if df_predict.empty:
        print("No leads found for prediction.")
        return

    features = ['region', 'product', 'customer_segment', 'call_duration_min', 
                'building_year', 'has_hohlraum', 'heating_system']
    targets = ['has_issues', 'has_scope_issue', 'has_time_issue', 
               'has_cavity_issue', 'has_temperature_issue']
    
    # Load Preprocessor
    preprocessor_path = os.path.join(MODEL_DIR, "preprocessor.joblib")
    if not os.path.exists(preprocessor_path):
        print("Error: Preprocessor not found. Please run training first.")
        return
    preprocessor = joblib.load(preprocessor_path)
    
    X_predict = df_predict[features]
    X_predict_preprocessed = preprocessor.transform(X_predict)
    feature_names = preprocessor.get_feature_names_out()
    
    predictions_lead = pd.DataFrame(index=df_predict.index)
    predictions_lead['lead_id'] = df_predict['lead_id']
    
    main_target_shap = None
    
    for target in targets:
        model_path = os.path.join(MODEL_DIR, f"model_{target}.joblib")
        if not os.path.exists(model_path):
            print(f"Warning: Model for {target} not found. Setting defaults.")
            predictions_lead[f"{target}_pred"] = 0
            predictions_lead[f"{target}_prob"] = 0.0
            continue
            
        model = joblib.load(model_path)
        
        # Predictions
        predictions_lead[f"{target}_pred"] = model.predict(X_predict_preprocessed)
        predictions_lead[f"{target}_prob"] = model.predict_proba(X_predict_preprocessed)[:, 1]
        
        if target == 'has_issues':
            explainer = shap.LinearExplainer(model, X_predict_preprocessed)
            main_target_shap = explainer.shap_values(X_predict_preprocessed)
    
    # Create meta column
    if main_target_shap is not None:
        print("Calculating top features for meta column...")
        top_features_list = []
        for i in range(len(df_predict)):
            top = get_top_features(main_target_shap[i], feature_names)
            top_features_list.append(json.dumps({"top_impact_features": top}))
        predictions_lead['meta'] = top_features_list
    
    # Move lead_id to the front
    cols = ['lead_id'] + [c for c in predictions_lead.columns if c != 'lead_id']
    predictions_lead = predictions_lead[cols]
    
    # Store lead predictions
    predictions_lead.to_sql('issue_predictions', engine, schema='prediction', if_exists='replace', index=False, dtype={'meta': Text})
    set_primary_key('prediction', 'issue_predictions', 'lead_id')
    
    print("Prediction pipeline completed successfully.")

if __name__ == "__main__":
    predict_and_save()
