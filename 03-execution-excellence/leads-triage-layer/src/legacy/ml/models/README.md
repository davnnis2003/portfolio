# ML Model Artifacts

This directory contains serialized trained models and preprocessing pipelines used for lead triage prediction.

## Important Note for Production
In a production environment, these `.joblib` files should **not** be stored in the git repository. They should be stored in cloud storage (e.g., **AWS S3**, Azure Blob Storage, or Google Cloud Storage).

### Proposed Production Workflow:
1.  **Training**: The training script ([`train_model.py`](../train_model.py)) runs in a training environment and uploads new artifacts to S3.
2.  **Prediction**: The prediction script ([`predict_leads.py`](../predict_leads.py)) downloads the latest artifacts from S3 on-demand or during initialization.

## Artifacts in this directory:
- `preprocessor.joblib`: The fitted preprocessing pipeline (Scaling, One-Hot Encoding).
- `model_has_issues.joblib`: Logistic Regression for general issue prediction.
- `model_has_scope_issue.joblib`: Logistic Regression for scope issues.
- `model_has_time_issue.joblib`: Logistic Regression for timing issues.
