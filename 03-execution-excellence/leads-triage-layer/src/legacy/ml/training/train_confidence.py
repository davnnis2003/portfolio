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

MODEL_DIR = "src/ml/models/confidence"
os.makedirs(MODEL_DIR, exist_ok=True)

def set_primary_key(schema, table, column):
    print(f"Setting primary key {column} on {schema}.{table}...")
    with engine.connect() as conn:
        conn.execute(text(f"ALTER TABLE {schema}.{table} ADD PRIMARY KEY ({column});"))
        conn.commit()

def load_data():
    print("Loading training data for confidence model...")
    query = "SELECT * FROM marts.confidence_training_data WHERE confidence_score > 0"
    df = pd.read_sql(query, engine)
    return df

def get_top_features(shap_values, feature_names, top_n=3):
    indices = np.argsort(np.abs(shap_values))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_values[i])} for i in indices]

def train_and_save():
    df = load_data()
    if df.empty:
        print("Error: No training data found.")
        return

    features = ['region', 'product', 'customer_segment', 'call_duration_min', 
                'building_year', 'has_hohlraum', 'heating_system', 'has_issues_prob']
    target = 'confidence_score'
    
    X = df[features]
    y = df[target]
    
    # Define preprocessing
    numeric_features = ['call_duration_min', 'building_year', 'has_issues_prob']
    categorical_features = ['region', 'product', 'customer_segment', 'has_hohlraum', 'heating_system']
    
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    X_preprocessed = preprocessor.fit_transform(X)
    feature_names = preprocessor.get_feature_names_out()
    
    # Save Preprocessor
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))
    
    # Feature Store: confidence_features
    df_features = pd.DataFrame(X_preprocessed, columns=feature_names)
    df_features['project_id'] = df['project_id'].values
    cols = ['project_id'] + [c for c in df_features.columns if c != 'project_id']
    df_features = df_features[cols]
    df_features.to_sql('confidence_features', engine, schema='feature_store', if_exists='replace', index=False)
    set_primary_key('feature_store', 'confidence_features', 'project_id')

    print("Training Confidence model (Logistic Regression)...")
    model = LogisticRegression(solver='lbfgs', max_iter=1000, class_weight='balanced')
    model.fit(X_preprocessed, y)
    
    joblib.dump(model, os.path.join(MODEL_DIR, "model_confidence.joblib"))
    
    # Generate training predictions for results table
    print("Generating training results...")
    df_results = df.copy()
    df_results['confidence_score_pred'] = model.predict(X_preprocessed)
    probs = model.predict_proba(X_preprocessed)
    for i, class_label in enumerate(model.classes_):
        df_results[f'confidence_score_prob_{class_label}'] = probs[:, i]
    
    print("Storing training results in prediction.confidence_training_results...")
    df_results.to_sql('confidence_training_results', engine, schema='prediction', if_exists='replace', index=False)
    set_primary_key('prediction', 'confidence_training_results', 'project_id')

    print("Calculating SHAP values for confidence model...")
    explainer = shap.LinearExplainer(model, X_preprocessed)
    shap_values = explainer.shap_values(X_preprocessed)
    
    # For multiclass, shap_values is a list of arrays (one per class)
    # We'll concatenate them with class labels
    all_shap_dfs = []
    for i, class_label in enumerate(model.classes_):
        # Handle 3D array (samples, features, classes) or list of arrays
        if isinstance(shap_values, list):
            class_shap = shap_values[i]
        elif len(shap_values.shape) == 3:
            class_shap = shap_values[:, :, i]
        else:
            class_shap = shap_values
            
        shap_df = pd.DataFrame(class_shap, columns=[f"class_{class_label}_shap_{f}" for f in feature_names])
        all_shap_dfs.append(shap_df)
    
    df_shap_all = pd.concat(all_shap_dfs, axis=1)
    df_shap_all['project_id'] = df['project_id'].values
    cols_shap = ['project_id'] + [c for c in df_shap_all.columns if c != 'project_id']
    df_shap_all = df_shap_all[cols_shap]
    
    print("Storing SHAP values in feature_store.confidence_shap_values...")
    df_shap_all.to_sql('confidence_shap_values', engine, schema='feature_store', if_exists='replace', index=False)
    set_primary_key('feature_store', 'confidence_shap_values', 'project_id')

    # Create meta column (explainability) for the predicted class
    print("Calculating top features for meta column...")
    top_features_list = []
    for i in range(len(df)):
        pred_class = df_results.iloc[i]['confidence_score_pred']
        class_idx = list(model.classes_).index(pred_class)
        row_shap = shap_values[i, :, class_idx] if len(shap_values.shape) == 3 else shap_values[class_idx][i]
        top = get_top_features(row_shap, feature_names)
        top_features_list.append(json.dumps({"top_impact_features": top}))
    
    df_results['meta'] = top_features_list
    
    print("Storing training results in prediction.confidence_training_results...")
    df_results.to_sql('confidence_training_results', engine, schema='prediction', if_exists='replace', index=False, dtype={'meta': Text})
    set_primary_key('prediction', 'confidence_training_results', 'project_id')
    
    print("Confidence model training completed.")

if __name__ == "__main__":
    train_and_save()
