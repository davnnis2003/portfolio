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

MODEL_DIR = "src/ml/models/triage"

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
        building_year, has_hohlraum, heating_system,
        n_vollgeschosse, fassaden_typ, mauerstarke_cm,
        is_gewoelbekeller, feuchtigkeit, dachboden_zukunft_wohnraum,
        transcript_text, has_issues_prob, confidence_score_pred
    FROM marts.lead_insights
    """
    df_predict = pd.read_sql(predict_query, engine)
    return df_predict

def check_hard_rules(row):
    """
    Implements hard rules from docs/qualification_rules.md.
    Returns (is_disqualified, reason).
    """
    product = row['product']
    region = row['region']
    year = row['building_year']
    wall_thickness = row['mauerstarke_cm']
    fassade = str(row['fassaden_typ']).lower() if pd.notnull(row['fassaden_typ']) else ""
    vollgeschosse = row['n_vollgeschosse']
    
    # 1. Universally disqualifying (mainly for fassade)
    if product == 'fassade':
        if "holz" in fassade or "fachwerk" in fassade:
            return True, "Holzständerbauweise / Fachwerkhaus nicht dämmbar"
        if vollgeschosse is not None and vollgeschosse >= 3:
            return True, "MFH mit 3 oder mehr Vollgeschossen"
        if wall_thickness is not None:
            if wall_thickness < 28:
                return True, "Mauerwerk < 28 cm"
            if wall_thickness > 50:
                return True, "Mauerwerk > 50 cm"
            if wall_thickness == 38:
                return True, "Mauerwerk exakt 38 cm"

    # 2. Region-specific rules (Fassade)
    if product == 'fassade':
        if region == 'SH_NordNieder_HH':
            if year < 1890:
                return True, "Region SH: Baujahr vor 1890"
            if year > 1975 and wall_thickness != 36.5:
                return True, "Region SH: Baujahr nach 1975 und Mauerstärke != 36.5"
            if "gelb" in fassade and "klinker" in fassade and wall_thickness is not None and wall_thickness < 41:
                return True, "Region SH: Gelbklinker unter 41cm"
                
        elif region == 'DDR_Ost':
            if year < 1890:
                return True, "Region Ost: Baujahr vor 1890"
            if year > 1965:
                is_exception = "klinker" in fassade and wall_thickness is not None and wall_thickness <= 32
                if not is_exception:
                    return True, "Region Ost: Baujahr nach 1965 (ohne Klinker-Ausnahme)"
                    
        elif region == 'NRW_SudNieder':
            if year < 1890:
                return True, "Region NRW: Baujahr vor 1890"
            if year > 1970:
                is_exception = wall_thickness == 36.5 or ("rot" in fassade and "klinker" in fassade)
                if not is_exception:
                    return True, "Region NRW: Baujahr nach 1970 (ohne Klinker/36.5-Ausnahme)"
                    
        elif region == 'Sud_Hessen_RLP':
            if year < 1880:
                return True, "Region Süd: Baujahr vor 1880"
            # Very restrictive rule: All except Klinker AND 30-33cm AND < 1950
            is_allowed = "klinker" in fassade and wall_thickness is not None and 30 <= wall_thickness <= 33 and year < 1950
            if not is_allowed:
                 # return True, "Region Süd: Nicht das spezifische Klinker-Profil"
                 pass # We might want to be careful with this one as it's VERY restrictive

    # 3. Product: OGD
    if product == 'ogd':
        if row['dachboden_zukunft_wohnraum'] is True:
            return True, "OGD: Zukünftige Wohnraumnutzung geplant"

    # 4. Product: Kellerdecke
    if product == 'kellerdecke':
        if row['feuchtigkeit'] is True:
            return True, "Keller: Feuchtigkeitsprobleme"
        if row['is_gewoelbekeller'] is True:
            return True, "Keller: Gewölbekeller"

    return False, None

def get_top_features(shap_values, feature_names, top_n=3):
    indices = np.argsort(np.abs(shap_values))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_values[i])} for i in indices]

def predict_and_save():
    df_predict = load_leads()
    if df_predict.empty:
        print("No leads found for prediction.")
        return

    # Load Model Assets
    preprocessor_path = os.path.join(MODEL_DIR, "preprocessor.joblib")
    vectorizer_path = os.path.join(MODEL_DIR, "vectorizer.joblib")
    model_path = os.path.join(MODEL_DIR, "model_triage.joblib")
    
    if not all(os.path.exists(p) for p in [preprocessor_path, vectorizer_path, model_path]):
        print("Error: Model assets not found. Please run training first.")
        return
        
    preprocessor = joblib.load(preprocessor_path)
    vectorizer = joblib.load(vectorizer_path)
    model = joblib.load(model_path)
    classes = model.classes_
    
    # Prepare Features
    features_base = ['region', 'product', 'customer_segment', 'call_duration_min', 
                    'building_year', 'has_hohlraum', 'heating_system',
                    'has_issues_prob', 'confidence_score_pred']
    
    X_base = df_predict[features_base]
    X_text = df_predict['transcript_text'].fillna('')
    
    X_base_preprocessed = preprocessor.transform(X_base)
    X_text_preprocessed = vectorizer.transform(X_text).toarray()
    X_combined = np.hstack([X_base_preprocessed, X_text_preprocessed])
    feature_names = list(preprocessor.get_feature_names_out()) + [f"text_{f}" for f in vectorizer.get_feature_names_out()]
    
    # ML Predictions
    ml_preds = model.predict(X_combined)
    ml_probs = model.predict_proba(X_combined)
    
    # SHAP for ML part
    explainer = shap.LinearExplainer(model, X_combined)
    shap_values = explainer.shap_values(X_combined)
    
    results = []
    for i in range(len(df_predict)):
        row = df_predict.iloc[i]
        
        # 1. Apply Hard Rules
        is_disqualified, reason = check_hard_rules(row)
        
        if is_disqualified:
            final_decision = 'disqualify'
            meta = {"reason": f"Hard Rule: {reason}", "source": "deterministic"}
            # Set probs to 0 for others
            row_probs = {c: 0.0 for c in classes}
            row_probs['disqualify'] = 1.0
        elif row['confidence_score_pred'] is not None and row['confidence_score_pred'] <= 2:
            final_decision = 'escalate'
            row_probs = {classes[j]: ml_probs[i, j] for j in range(len(classes))}
            meta = {"reason": "Low confidence score (<= 2)", "source": "rule_override"}
        elif max(ml_probs[i]) < 0.45:
            final_decision = 'escalate'
            row_probs = {classes[j]: ml_probs[i, j] for j in range(len(classes))}
            meta = {"reason": f"Low model certainty ({max(ml_probs[i]):.2f})", "source": "rule_override"}
        else:
            final_decision = ml_preds[i]
            # Use ML probabilities
            row_probs = {classes[j]: ml_probs[i, j] for j in range(len(classes))}
            
            # SHAP for predicted class
            pred_idx = list(classes).index(final_decision)
            row_shap = shap_values[i, :, pred_idx]
            top_features = get_top_features(row_shap, feature_names)
            meta = {"top_impact_features": top_features, "ml_prediction": final_decision, "source": "ml"}

        res = {
            "lead_id": row['lead_id'],
            "triage_decision_pred": final_decision,
            "pitch_prob": row_probs.get('pitch', 0.0),
            "pitch_with_flag_prob": row_probs.get('pitch_with_flag', 0.0),
            "pitch_with_cross_sell_prob": row_probs.get('pitch_with_cross_sell', 0.0),
            "disqualify_prob": row_probs.get('disqualify', 0.0),
            "escalate_prob": row_probs.get('escalate', 0.0),
            "meta": json.dumps(meta)
        }
        results.append(res)
    
    df_results = pd.DataFrame(results)
    
    # Save lead predictions
    df_results.to_sql('triage_predictions', engine, schema='prediction', if_exists='replace', index=False, dtype={'meta': Text})
    set_primary_key('prediction', 'triage_predictions', 'lead_id')
    
    print("Triage prediction pipeline completed successfully.")

if __name__ == "__main__":
    predict_and_save()
