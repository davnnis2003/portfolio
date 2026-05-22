from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class LeadInput(BaseModel):
    lead_id: Optional[str] = None
    region: str
    product: str
    customer_segment: str
    call_duration_min: float
    building_year: int
    has_hohlraum: bool
    heating_system: str
    # Issues → Confidence dependency
    has_issues_prob: Optional[float] = None
    # Confidence → Triage dependency
    confidence_score_pred: Optional[float] = None
    # Triage text feature
    transcript_text: Optional[str] = None
    # Hard-rule fields (triage)
    n_vollgeschosse: Optional[float] = None
    fassaden_typ: Optional[str] = None
    mauerstarke_cm: Optional[float] = None
    is_gewoelbekeller: Optional[bool] = None
    feuchtigkeit: Optional[bool] = None
    dachboden_zukunft_wohnraum: Optional[bool] = None


class IssuesPrediction(BaseModel):
    has_issues_pred: int
    has_issues_prob: float
    has_scope_issue_pred: int
    has_scope_issue_prob: float
    has_time_issue_pred: int
    has_time_issue_prob: float
    meta: dict


class ConfidencePrediction(BaseModel):
    confidence_score_pred: int
    confidence_score_probs: dict[str, float]
    meta: dict


class TriagePrediction(BaseModel):
    triage_decision: str
    probabilities: dict[str, float]
    meta: dict


class PipelinePrediction(BaseModel):
    lead_id: Optional[str]
    issues: IssuesPrediction
    confidence: ConfidencePrediction
    triage: TriagePrediction


from interpretation_layer.llm_parser.parser import (
    EntityInfo as LLMParserEntityInfo,
    Contradiction as LLMParserContradiction,
    RiskFactor as LLMParserRiskFactor,
    ParsedLead as LLMParserOutput
)

class DecisionRequest(BaseModel):
    lead_id: Optional[str] = None
    transcript_text: str
    intake_data: dict

class DecisionResponse(BaseModel):
    lead_id: Optional[str] = None
    decision: str
    confidence_score: int
    reasoning: list[str]
    rule_status: str
    rule_reasons: list[str]
    llm_analysis: dict
    memory_stats: dict


class RuleEngineResponse(BaseModel):
    rule_status: str
    rule_reasons: list[str]


