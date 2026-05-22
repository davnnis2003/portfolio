import json
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from decision_layer.decision_engine import DecisionEngine
from decision_layer.briefing.generator import BriefingGenerator, FieldBriefing, BriefingBullet
from api.schemas import DecisionRequest

router = APIRouter(prefix="/briefing", tags=["briefing"])

# ---------------------------------------------------------------------------
# Singleton instances (lazy-loaded)
# ---------------------------------------------------------------------------
_engine_instance: Optional[DecisionEngine] = None
_generator_instance: Optional[BriefingGenerator] = None


def get_engine() -> DecisionEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DecisionEngine(memory_limit=20)
    return _engine_instance


def get_generator() -> BriefingGenerator:
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = BriefingGenerator()
    return _generator_instance


# ---------------------------------------------------------------------------
# Response schema (mirrors FieldBriefing for the API layer)
# ---------------------------------------------------------------------------

class BriefingBulletResponse(BaseModel):
    label: str
    text: str


class BriefingResponse(BaseModel):
    lead_id: Optional[str] = None
    decision: str
    confidence_pct: int
    bullets: List[BriefingBulletResponse]
    raw_text: str  # Added for parity and debugging


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/generate", response_model=BriefingResponse)
def generate_briefing(
    request: DecisionRequest,
    engine: DecisionEngine = Depends(get_engine),
    generator: BriefingGenerator = Depends(get_generator),
):
    """
    Run the Decision Engine on a lead and return a structured field briefing.

    Accepts the same request body as ``POST /decision/evaluate``.
    Returns 4–6 actionable bullet points for the field representative.
    
    NOTE: If the intake_data contains a '_decision' key, this endpoint will
    use that pre-computed decision instead of re-running the engine.
    """
    try:
        # Check if we have a pre-computed decision from an earlier pipeline step
        # This prevents "decision flips" and saves compute.
        precomputed = request.intake_data.get("_decision")
        
        if precomputed and "decision" in precomputed:
            from decision_layer.decision_engine import DecisionOutput, TriageDecision
            from memory_layer.models import AggregateStats
            from api.schemas import LLMParserOutput
            
            # Reconstruct DecisionOutput from the provided data
            # This ensures the briefing matches exactly what was saved in step 4
            decision_output = DecisionOutput(
                lead_id=precomputed.get("lead_id"),
                decision=TriageDecision(precomputed["decision"]),
                confidence_score=precomputed.get("confidence_score", 0),
                reasoning=precomputed.get("reasoning", []),
                rule_status=precomputed.get("rule_status", "UNKNOWN"),
                rule_reasons=precomputed.get("rule_reasons", []),
                llm_analysis=LLMParserOutput.model_validate(precomputed["llm_analysis"]),
                memory_stats=AggregateStats.model_validate(precomputed["memory_stats"])
            )
        else:
            # Fallback to running the engine if no decision is provided
            decision_output = engine.decide(request.intake_data, request.transcript_text)
            
        briefing: FieldBriefing = generator.generate(decision_output)

        result = BriefingResponse(
            lead_id=briefing.lead_id,
            decision=briefing.decision,
            confidence_pct=briefing.confidence_pct,
            bullets=[
                BriefingBulletResponse(label=b.label, text=b.text)
                for b in briefing.bullets
            ],
            raw_text=briefing.raw_text,
        )

        # Return indented JSON for better readability in showcase
        return Response(
            content=json.dumps(result.model_dump(), indent=2, ensure_ascii=False),
            media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
