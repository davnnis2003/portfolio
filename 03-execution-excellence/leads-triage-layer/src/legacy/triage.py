from __future__ import annotations

import numpy as np
import pandas as pd
import shap
from fastapi import APIRouter, HTTPException

from legacy.model_loader import get_models
from api.schemas import LeadInput, TriagePrediction

router = APIRouter(prefix="/predict", tags=["triage"])

_BASE_FEATURES = [
    "region", "product", "customer_segment", "call_duration_min",
    "building_year", "has_hohlraum", "heating_system",
    "has_issues_prob", "confidence_score_pred",
]


def _top_features(shap_vals: np.ndarray, feature_names, top_n: int = 3) -> list[dict]:
    idx = np.argsort(np.abs(shap_vals))[-top_n:][::-1]
    return [{"feature": feature_names[i], "impact": float(shap_vals[i])} for i in idx]


def _check_hard_rules(lead: LeadInput) -> tuple[bool, str | None]:
    product = lead.product
    region = lead.region
    year = lead.building_year
    wall = lead.mauerstarke_cm
    fassade = str(lead.fassaden_typ).lower() if lead.fassaden_typ else ""
    floors = lead.n_vollgeschosse

    if product == "fassade":
        if "holz" in fassade or "fachwerk" in fassade:
            return True, "Holzständerbauweise / Fachwerkhaus nicht dämmbar"
        if floors is not None and floors >= 3:
            return True, "MFH mit 3 oder mehr Vollgeschossen"
        if wall is not None:
            if wall < 28:
                return True, "Mauerwerk < 28 cm"
            if wall > 50:
                return True, "Mauerwerk > 50 cm"
            if wall == 38:
                return True, "Mauerwerk exakt 38 cm"

        if region == "SH_NordNieder_HH":
            if year < 1890:
                return True, "Region SH: Baujahr vor 1890"
            if year > 1975 and wall != 36.5:
                return True, "Region SH: Baujahr nach 1975 und Mauerstärke != 36.5"
            if "gelb" in fassade and "klinker" in fassade and wall is not None and wall < 41:
                return True, "Region SH: Gelbklinker unter 41cm"
        elif region == "DDR_Ost":
            if year < 1890:
                return True, "Region Ost: Baujahr vor 1890"
            if year > 1965:
                is_exception = "klinker" in fassade and wall is not None and wall <= 32
                if not is_exception:
                    return True, "Region Ost: Baujahr nach 1965 (ohne Klinker-Ausnahme)"
        elif region == "NRW_SudNieder":
            if year < 1890:
                return True, "Region NRW: Baujahr vor 1890"
            if year > 1970:
                is_exception = wall == 36.5 or ("rot" in fassade and "klinker" in fassade)
                if not is_exception:
                    return True, "Region NRW: Baujahr nach 1970 (ohne Klinker/36.5-Ausnahme)"
        elif region == "Sud_Hessen_RLP":
            if year < 1880:
                return True, "Region Süd: Baujahr vor 1880"

    if product == "ogd" and lead.dachboden_zukunft_wohnraum:
        return True, "OGD: Zukünftige Wohnraumnutzung geplant"

    if product == "kellerdecke":
        if lead.feuchtigkeit:
            return True, "Keller: Feuchtigkeitsprobleme"
        if lead.is_gewoelbekeller:
            return True, "Keller: Gewölbekeller"

    return False, None


def predict_triage(lead: LeadInput) -> TriagePrediction:
    if lead.has_issues_prob is None or lead.confidence_score_pred is None:
        raise HTTPException(
            status_code=422,
            detail="`has_issues_prob` and `confidence_score_pred` are required. "
                   "Run /predict/pipeline or supply them directly.",
        )

    m = get_models().triage

    # Hard rules
    disqualified, reason = _check_hard_rules(lead)
    if disqualified:
        classes = list(m.classes)
        probs = {c: 0.0 for c in classes}
        probs["disqualify"] = 1.0
        return TriagePrediction(
            triage_decision="disqualify",
            probabilities=probs,
            meta={"reason": f"Hard Rule: {reason}", "source": "deterministic"},
        )

    row_base = pd.DataFrame([{f: getattr(lead, f) for f in _BASE_FEATURES}])
    X_base = m.preprocessor.transform(row_base)
    X_text = m.vectorizer.transform([lead.transcript_text or ""]).toarray()
    X = np.hstack([X_base, X_text])
    feature_names = list(m.preprocessor.get_feature_names_out()) + [
        f"text_{f}" for f in m.vectorizer.get_feature_names_out()
    ]

    ml_pred = m.model.predict(X)[0]
    ml_probs = m.model.predict_proba(X)[0]
    classes = list(m.model.classes_)
    row_probs = {c: float(p) for c, p in zip(classes, ml_probs)}

    # Rule overrides
    if lead.confidence_score_pred <= 2:
        return TriagePrediction(
            triage_decision="escalate",
            probabilities=row_probs,
            meta={"reason": "Low confidence score (<= 2)", "source": "rule_override"},
        )
    if max(ml_probs) < 0.45:
        return TriagePrediction(
            triage_decision="escalate",
            probabilities=row_probs,
            meta={"reason": f"Low model certainty ({max(ml_probs):.2f})", "source": "rule_override"},
        )

    explainer = shap.LinearExplainer(m.model, X)
    shap_vals = explainer.shap_values(X)
    pred_idx = classes.index(ml_pred)
    row_shap = shap_vals[0, :, pred_idx]
    top = _top_features(row_shap, feature_names)

    return TriagePrediction(
        triage_decision=ml_pred,
        probabilities=row_probs,
        meta={"top_impact_features": top, "ml_prediction": ml_pred, "source": "ml"},
    )


@router.post("/triage", response_model=TriagePrediction)
def predict_triage_endpoint(lead: LeadInput) -> TriagePrediction:
    return predict_triage(lead)
