from __future__ import annotations

import json

import numpy as np
import pandas as pd
import shap
from fastapi import APIRouter

from legacy.model_loader import get_models
from api.schemas import IssuesPrediction, LeadInput

router = APIRouter(prefix="/predict", tags=["issues"])

_FEATURES = [
    "region", "product", "customer_segment", "call_duration_min",
    "building_year", "has_hohlraum", "heating_system",
]


def _top_features(shap_vals: np.ndarray, feature_names, top_n: int = 3) -> list[dict]:
    idx = np.argsort(np.abs(shap_vals))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_vals[i])} for i in idx]


def predict_issues(lead: LeadInput) -> IssuesPrediction:
    m = get_models().issues
    row = pd.DataFrame([{f: getattr(lead, f) for f in _FEATURES}])
    X = m.preprocessor.transform(row)
    feature_names = m.preprocessor.get_feature_names_out()

    has_issues_pred = int(m.has_issues.predict(X)[0])
    has_issues_prob = float(m.has_issues.predict_proba(X)[0, 1])
    has_scope_pred = int(m.has_scope_issue.predict(X)[0])
    has_scope_prob = float(m.has_scope_issue.predict_proba(X)[0, 1])
    has_time_pred = int(m.has_time_issue.predict(X)[0])
    has_time_prob = float(m.has_time_issue.predict_proba(X)[0, 1])

    explainer = shap.LinearExplainer(m.has_issues, X)
    shap_vals = explainer.shap_values(X)
    top = _top_features(shap_vals[0], feature_names)

    return IssuesPrediction(
        has_issues_pred=has_issues_pred,
        has_issues_prob=has_issues_prob,
        has_scope_issue_pred=has_scope_pred,
        has_scope_issue_prob=has_scope_prob,
        has_time_issue_pred=has_time_pred,
        has_time_issue_prob=has_time_prob,
        meta={"top_impact_features": top},
    )


@router.post("/issues", response_model=IssuesPrediction)
def predict_issues_endpoint(lead: LeadInput) -> IssuesPrediction:
    return predict_issues(lead)
