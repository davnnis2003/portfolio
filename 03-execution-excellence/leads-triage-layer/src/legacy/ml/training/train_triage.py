import os
import pandas as pd
import numpy as np
import joblib
import json
from sqlalchemy import create_engine, text, Text
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_extraction.text import TfidfVectorizer
import shap
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
os.makedirs(MODEL_DIR, exist_ok=True)

def set_primary_key(schema, table, column):
    print(f"Setting primary key {column} on {schema}.{table}...")
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {schema}.{table} ADD PRIMARY KEY ({column});"))
        conn.commit()

def load_data():
    print("Loading training data from database...")
    train_query = """
    SELECT 
        project_id, region, product, customer_segment, call_duration_min, 
        building_year, has_hohlraum, heating_system,
        has_issues_prob, confidence_score_pred,
        sales_call_summary, triage_labels
    FROM marts.project_insights
    """
    df_train = pd.read_sql(train_query, engine)
    return df_train

def get_top_features(shap_values, feature_names, top_n=3):
    # For multi-class, shap_values is a list of arrays (one per class)
    # We'll simplify and just look at the magnitude across all classes or pick one.
    # Actually, let's just return something useful for explainability.
    if isinstance(shap_values, list):
        # Average absolute SHAP across classes
        avg_shap = np.mean([np.abs(s) for s in shap_values], axis=0)
        indices = np.argsort(avg_shap)[-top_n:][::-1]
    else:
        indices = np.argsort(np.abs(shap_values))[-top_n:][::-1]
    
    return [{"feature": feature_names[i], "impact": float(np.mean([s[i] for s in shap_values])) if isinstance(shap_values, list) else float(shap_values[i])} for i in indices]

def train_and_save():
    df_train = load_data()
    if df_train.empty:
        print("Error: No training data found.")
        return

    # Filter out any rows without labels
    df_train = df_train[df_train['triage_labels'].notnull()]
    
    features_base = ['region', 'product', 'customer_segment', 'call_duration_min', 
                    'building_year', 'has_hohlraum', 'heating_system',
                    'has_issues_prob', 'confidence_score_pred']
    
    X_train = df_train[features_base]
    X_text = df_train['sales_call_summary'].fillna('')
    y = df_train['triage_labels']
    
    # Define preprocessing
    numeric_features = ['call_duration_min', 'building_year', 'has_issues_prob', 'confidence_score_pred']
    categorical_features = ['region', 'product', 'customer_segment', 'has_hohlraum', 'heating_system']
    
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Text Transformer
    text_transformer = TfidfVectorizer(max_features=100)
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    X_base_preprocessed = preprocessor.fit_transform(X_train)
    X_text_preprocessed = text_transformer.fit_transform(X_text).toarray()
    
    X_combined = np.hstack([X_base_preprocessed, X_text_preprocessed])
    
    feature_names = list(preprocessor.get_feature_names_out()) + [f"text_{f}" for f in text_transformer.get_feature_names_out()]
    
    # Save Preprocessor and Vectorizer
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))
    joblib.dump(text_transformer, os.path.join(MODEL_DIR, "vectorizer.joblib"))
    
    # Train Multi-class model
    print("Training multi-class triage model...")
    model = LogisticRegression(max_iter=1000)
    model.fit(X_combined, y)
    joblib.dump(model, os.path.join(MODEL_DIR, "model_triage.joblib"))
    joblib.dump(model.classes_, os.path.join(MODEL_DIR, "classes.joblib"))
    
    # Predictions and Probs
    probs = model.predict_proba(X_combined)
    preds = model.predict(X_combined)
    
    df_results = df_train.copy()
    df_results['triage_decision_pred'] = preds
    
    for i, class_name in enumerate(model.classes_):
        df_results[f"{class_name}_prob"] = probs[:, i]
    
    # SHAP Values (Simplified for multi-class)
    print("Calculating SHAP values...")
    explainer = shap.LinearExplainer(model, X_combined)
    shap_values = explainer.shap_values(X_combined)
    
    # Create meta column
    print(f"SHAP values type: {type(shap_values)}")
    if isinstance(shap_values, list):
        print(f"SHAP values list length: {len(shap_values)}")
        print(f"SHAP values[0] shape: {shap_values[0].shape}")
    else:
        print(f"SHAP values shape: {shap_values.shape}")
    
    print("Calculating top features for meta column...")
    top_features_list = []
    for i in range(len(df_train)):
        # For meta, we'll use SHAP values for the predicted class
        pred_idx = list(model.classes_).index(preds[i])
        row_shap = shap_values[i, :, pred_idx]
        top = get_top_features(row_shap, feature_names)
        top_features_list.append(json.dumps({"top_impact_features": top, "predicted_class": preds[i]}))
    
    df_results['meta'] = top_features_list
    
    # Save training results
    df_results.to_sql('triage_training_results', engine, schema='prediction', if_exists='replace', index=False, dtype={'meta': Text})
    set_primary_key('prediction', 'triage_training_results', 'project_id')
    
    print("Triage training pipeline completed successfully.")

if __name__ == "__main__":
    train_and_save()
