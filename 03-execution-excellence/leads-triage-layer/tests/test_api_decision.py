import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app
from decision_layer.decision_engine import DecisionOutput, TriageDecision
from interpretation_layer.llm_parser.parser import ParsedLead, EntityInfo
from memory_layer.models import AggregateStats

client = TestClient(app)

def test_evaluate_decision_endpoint():
    payload = {
        "transcript_text": "Sample transcript",
        "intake_data": {
            "lead_id": "TEST-123",
            "product": "fassade"
        }
    }
    
    mock_output = DecisionOutput(
        lead_id="TEST-123",
        decision=TriageDecision.PITCH,
        confidence_score=5,
        reasoning=["All good"],
        rule_status="QUALIFIED",
        rule_reasons=[],
        llm_analysis=ParsedLead(entities=EntityInfo(), contradictions=[], risk_factors=[]),
        memory_stats=AggregateStats(total_similar=5, close_rate=0.8, avg_overrun_eur=0.0, common_issues=[])
    )
    
    with patch('api.routers.decision.DecisionEngine.decide') as mock_decide:
        mock_decide.return_value = mock_output
        
        response = client.post("/decision/evaluate", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "pitch"
        assert data["confidence_score"] == 5
        assert data["lead_id"] == "TEST-123"
