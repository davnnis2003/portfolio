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

MODEL_DIR = "src/ml/models/issues"
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
        has_issues, has_scope_issue, has_time_issue, 
        has_cavity_issue, has_temperature_issue
    FROM marts.project_insights
    """
    df_train = pd.read_sql(train_query, engine)
    return df_train

def get_top_features(shap_values, feature_names, top_n=3):
    indices = np.argsort(np.abs(shap_values))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_values[i])} for i in indices]

def train_and_save():
    df_train = load_data()
    if df_train.empty:
        print("Error: No training data found.")
        return

    features = ['region', 'product', 'customer_segment', 'call_duration_min', 
                'building_year', 'has_hohlraum', 'heating_system']
    targets = ['has_issues', 'has_scope_issue', 'has_time_issue', 
               'has_cavity_issue', 'has_temperature_issue']
    
    X_train = df_train[features]
    
    # Define preprocessing
    numeric_features = ['call_duration_min', 'building_year']
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
    
    X_train_preprocessed = preprocessor.fit_transform(X_train)
    feature_names = preprocessor.get_feature_names_out()
    
    # Save Preprocessor
    joblib.dump(preprocessor, os.path.join(MODEL_DIR, "preprocessor.joblib"))
    
    # Feature Store: project_features
    df_features_train = pd.DataFrame(X_train_preprocessed, columns=feature_names)
    df_features_train['project_id'] = df_train['project_id'].values
    cols = ['project_id'] + [c for c in df_features_train.columns if c != 'project_id']
    df_features_train = df_features_train[cols]
    df_features_train.to_sql('issue_features', engine, schema='feature_store', if_exists='replace', index=False)
    set_primary_key('feature_store', 'issue_features', 'project_id')

    models = {}
    all_shap_values = []
    predictions_train = pd.DataFrame(index=df_train.index)
    
    main_target_shap = None
    
    for target in targets:
        print(f"Training model for {target}...")
        y = df_train[target].astype(int)
        
        if len(np.unique(y)) < 2:
            print(f"Warning: Only one class found for {target}. Setting defaults.")
            predictions_train[f"{target}_pred"] = 0
            predictions_train[f"{target}_prob"] = 0.0
            continue

        model = LogisticRegression(max_iter=1000)
        model.fit(X_train_preprocessed, y)
        joblib.dump(model, os.path.join(MODEL_DIR, f"model_{target}.joblib"))
        
        # Predictions
        predictions_train[f"{target}_pred"] = model.predict(X_train_preprocessed)
        predictions_train[f"{target}_prob"] = model.predict_proba(X_train_preprocessed)[:, 1]
        
        # SHAP Values
        explainer = shap.LinearExplainer(model, X_train_preprocessed)
        shap_values = explainer.shap_values(X_train_preprocessed)
        
        if target == 'has_issues':
            main_target_shap = shap_values
            
        shap_df = pd.DataFrame(shap_values, columns=[f"{target}_shap_{f}" for f in feature_names])
        all_shap_values.append(shap_df)
    
    # Create meta column
    if main_target_shap is not None:
        print("Calculating top features for meta column...")
        top_features_list = []
        for i in range(len(df_train)):
            top = get_top_features(main_target_shap[i], feature_names)
            top_features_list.append(json.dumps({"top_impact_features": top}))
        predictions_train['meta'] = top_features_list

    # Prediction results: training_results
    df_train_results = pd.concat([df_train, predictions_train], axis=1)
    df_train_results.to_sql('issue_training_results', engine, schema='prediction', if_exists='replace', index=False, dtype={'meta': Text})
    set_primary_key('prediction', 'issue_training_results', 'project_id')
    
    # Store SHAP values
    if all_shap_values:
        df_shap_all = pd.concat(all_shap_values, axis=1)
        df_shap_all['project_id'] = df_train['project_id'].values
        cols_shap = ['project_id'] + [c for c in df_shap_all.columns if c != 'project_id']
        df_shap_all = df_shap_all[cols_shap]
        df_shap_all.to_sql('issue_shap_values', engine, schema='feature_store', if_exists='replace', index=False)
        set_primary_key('feature_store', 'issue_shap_values', 'project_id')
    
    print("Training pipeline completed successfully.")

if __name__ == "__main__":
    train_and_save()
