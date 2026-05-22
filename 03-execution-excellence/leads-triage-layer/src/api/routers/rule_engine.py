from fastapi import APIRouter, HTTPException
from interpretation_layer.rule_engine import RuleEngine
from api.schemas import RuleEngineResponse
from typing import Dict, Any

router = APIRouter(prefix="/rule-engine", tags=["rule-engine"])

@router.post("/evaluate", response_model=RuleEngineResponse)
def evaluate_rules(intake_data: Dict[str, Any]):
    """
    Evaluate deterministic building rules against intake data.
    """
    try:
        engine = RuleEngine()
        status, reasons = engine.evaluate(intake_data)
        return RuleEngineResponse(
            rule_status=status,
            rule_reasons=reasons
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
