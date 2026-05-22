from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import joblib

_MODELS_DIR = Path(__file__).resolve().parents[2] / "src" / "legacy" / "ml" / "models"


@dataclass
class IssuesModels:
    preprocessor: Any
    has_issues: Any
    has_scope_issue: Any
    has_time_issue: Any


@dataclass
class ConfidenceModels:
    preprocessor: Any
    model: Any


@dataclass
class TriageModels:
    preprocessor: Any
    vectorizer: Any
    model: Any
    classes: Any


@dataclass
class AllModels:
    issues: IssuesModels
    confidence: ConfidenceModels
    triage: TriageModels


_cache: AllModels | None = None


def _load_issues() -> IssuesModels:
    d = _MODELS_DIR / "issues"
    return IssuesModels(
        preprocessor=joblib.load(d / "preprocessor.joblib"),
        has_issues=joblib.load(d / "model_has_issues.joblib"),
        has_scope_issue=joblib.load(d / "model_has_scope_issue.joblib"),
        has_time_issue=joblib.load(d / "model_has_time_issue.joblib"),
    )


def _load_confidence() -> ConfidenceModels:
    d = _MODELS_DIR / "confidence"
    return ConfidenceModels(
        preprocessor=joblib.load(d / "preprocessor.joblib"),
        model=joblib.load(d / "model_confidence.joblib"),
    )


def _load_triage() -> TriageModels:
    d = _MODELS_DIR / "triage"
    return TriageModels(
        preprocessor=joblib.load(d / "preprocessor.joblib"),
        vectorizer=joblib.load(d / "vectorizer.joblib"),
        model=joblib.load(d / "model_triage.joblib"),
        classes=joblib.load(d / "classes.joblib"),
    )


def get_models() -> AllModels:
    global _cache
    if _cache is None:
        _cache = AllModels(
            issues=_load_issues(),
            confidence=_load_confidence(),
            triage=_load_triage(),
        )
    return _cache
