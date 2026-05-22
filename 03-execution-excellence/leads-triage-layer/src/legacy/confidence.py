from __future__ import annotations

import json

import numpy as np
import pandas as pd
import shap
from fastapi import APIRouter, HTTPException

from legacy.model_loader import get_models
from api.schemas import ConfidencePrediction, LeadInput

router = APIRouter(prefix="/predict", tags=["confidence"])

_FEATURES = [
    "region", "product", "customer_segment", "call_duration_min",
    "building_year", "has_hohlraum", "heating_system", "has_issues_prob",
]


def _top_features(shap_vals: np.ndarray, feature_names, top_n: int = 3) -> list[dict]:
    idx = np.argsort(np.abs(shap_vals))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_vals[i])} for i in idx]


def predict_confidence(lead: LeadInput) -> ConfidencePrediction:
    if lead.has_issues_prob is None:
        raise HTTPException(
            status_code=422,
            detail="`has_issues_prob` is required for confidence prediction. "
                   "Run /predict/issues first or supply it directly.",
        )
    m = get_models().confidence
    row = pd.DataFrame([{f: getattr(lead, f) for f in _FEATURES}])
    X = m.preprocessor.transform(row)
    feature_names = m.preprocessor.get_feature_names_out()

    score_pred = int(m.model.predict(X)[0])
    probs = m.model.predict_proba(X)[0]
    score_probs = {str(c): float(p) for c, p in zip(m.model.classes_, probs)}

    explainer = shap.LinearExplainer(m.model, X)
    shap_vals = explainer.shap_values(X)

    # shap_vals may be (n_samples, n_features, n_classes) or list
    pred_idx = list(m.model.classes_).index(score_pred)
    if isinstance(shap_vals, list):
        row_shap = shap_vals[pred_idx][0]
    else:
        row_shap = shap_vals[0, :, pred_idx] if shap_vals.ndim == 3 else shap_vals[0]

    top = _top_features(row_shap, feature_names)

    return ConfidencePrediction(
        confidence_score_pred=score_pred,
        confidence_score_probs=score_probs,
        meta={"top_impact_features": top},
    )


@router.post("/confidence", response_model=ConfidencePrediction)
def predict_confidence_endpoint(lead: LeadInput) -> ConfidencePrediction:
    return predict_confidence(lead)
