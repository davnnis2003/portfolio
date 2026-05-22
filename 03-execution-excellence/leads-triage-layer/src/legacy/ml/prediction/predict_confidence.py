import os
import pandas as pd
import numpy as np
import joblib
import shap
import json
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

MODEL_DIR = "src/ml/models/confidence"

def set_primary_key(schema, table, column):
    print(f"Setting primary key {column} on {schema}.{table}...")
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {schema}.{table} ADD PRIMARY KEY ({column});"))
        conn.commit()

def get_top_features(shap_values, feature_names, top_n=3):
    indices = np.argsort(np.abs(shap_values))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_values[i])} for i in indices]

def load_leads():
    print("Loading lead data for confidence prediction...")
    # Join lead_insights with predicted issue probabilities from staging
    query = """
    SELECT 
        l.lead_id, l.region, l.product, l.customer_segment, l.call_duration_min, 
        l.building_year, l.has_hohlraum, l.heating_system,
        p.has_issues_prob
    FROM marts.lead_insights l
    JOIN staging.issue_predictions p ON l.lead_id = p.lead_id
    """
    df = pd.read_sql(query, engine)
    return df

def predict_and_save():
    df = load_leads()
    if df.empty:
        print("No leads found for prediction.")
        return

    features = ['region', 'product', 'customer_segment', 'call_duration_min', 
                'building_year', 'has_hohlraum', 'heating_system', 'has_issues_prob']
    
    # Load Preprocessor and Model
    preprocessor_path = os.path.join(MODEL_DIR, "preprocessor.joblib")
    model_path = os.path.join(MODEL_DIR, "model_confidence.joblib")
    
    if not os.path.exists(preprocessor_path) or not os.path.exists(model_path):
        print("Error: Model or preprocessor not found. Please run training first.")
        return
        
    preprocessor = joblib.load(preprocessor_path)
    model = joblib.load(model_path)
    
    X = df[features]
    X_preprocessed = preprocessor.transform(X)
    feature_names = preprocessor.get_feature_names_out()
    
    print("Generating confidence score predictions...")
    predictions = pd.DataFrame(index=df.index)
    predictions['lead_id'] = df['lead_id']
    predictions['confidence_score_pred'] = model.predict(X_preprocessed)
    
    # Probabilities for each class (1-5)
    probs = model.predict_proba(X_preprocessed)
    for i, class_label in enumerate(model.classes_):
        predictions[f'confidence_score_prob_{class_label}'] = probs[:, i]
    
    # SHAP Explainability
    print("Calculating SHAP values for explainability...")
    explainer = shap.LinearExplainer(model, X_preprocessed)
    shap_values = explainer.shap_values(X_preprocessed)
    
    top_features_list = []
    for i in range(len(df)):
        pred_class = predictions.iloc[i]['confidence_score_pred']
        class_idx = list(model.classes_).index(pred_class)
        row_shap = shap_values[i, :, class_idx] if len(shap_values.shape) == 3 else shap_values[class_idx][i]
        top = get_top_features(row_shap, feature_names)
        top_features_list.append(json.dumps({"top_impact_features": top}))
    
    predictions['meta'] = top_features_list
    
    # Store results
    print("Storing confidence predictions in prediction.confidence_predictions...")
    predictions.to_sql('confidence_predictions', engine, schema='prediction', if_exists='replace', index=False, dtype={'meta': Text})
    set_primary_key('prediction', 'confidence_predictions', 'lead_id')
    
    print("Confidence prediction pipeline completed successfully.")

if __name__ == "__main__":
    predict_and_save()
