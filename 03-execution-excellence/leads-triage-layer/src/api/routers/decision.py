from fastapi import APIRouter, HTTPException, Depends
from decision_layer.decision_engine import DecisionEngine
from api.schemas import DecisionRequest, DecisionResponse
import json
from fastapi.responses import Response

router = APIRouter(prefix="/decision", tags=["decision"])

# Singleton instance for decision engine (lazy loaded)
_engine_instance = None

def get_engine():
    global _engine_instance
    if _engine_instance is None:
        # Using a standard limit for the case study showcase to match memory service
        _engine_instance = DecisionEngine(memory_limit=100)
    return _engine_instance

@router.post("/evaluate", response_model=DecisionResponse)
def evaluate_lead(request: DecisionRequest, engine: DecisionEngine = Depends(get_engine)):
    """
    Run the full decision engine on a lead: Rules + LLM + Memory.
    """
    try:
        result = engine.decide(request.intake_data, request.transcript_text)
        
        # Return indented JSON for better readability in showcase
        return Response(
            content=json.dumps(result.model_dump(), indent=2),
            media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
