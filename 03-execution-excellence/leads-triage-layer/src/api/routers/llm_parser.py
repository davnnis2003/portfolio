import json
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from typing import Dict, Any
from interpretation_layer.llm_parser.parser import LLMParser, ParsedLead

router = APIRouter(prefix="/llm-parser", tags=["llm-parser"])

class ParseRequest(BaseModel):
    transcript_text: str
    intake_data: Dict[str, Any]

@router.post("/parse")
def parse_lead(request: ParseRequest):
    """
    Extract entities, contradictions, and risks from a transcript and intake data.
    """
    try:
        parser = LLMParser()
        result = parser.parse(request.transcript_text, request.intake_data)
        # Return indented JSON for better readability in curl/showcase
        return Response(
            content=json.dumps(result.model_dump(), indent=2),
            media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
