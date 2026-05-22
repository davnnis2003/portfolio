from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app

client = TestClient(app)

@patch('interpretation_layer.llm_parser.parser.LLMParser.parse')
def test_api_parse_endpoint(mock_parse):
    # Mock the parser's parse method
    from interpretation_layer.llm_parser.parser import ParsedLead, EntityInfo
    
    mock_parse.return_value = ParsedLead(
        entities=EntityInfo(house_type="Bungalow"),
        contradictions=[],
        risk_factors=[]
    )
    
    response = client.post(
        "/llm-parser/parse",
        json={
            "transcript_text": "Hello, I have a bungalow.",
            "intake_data": {"lead_id": "L123"}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["entities"]["house_type"] == "Bungalow"
    assert "contradictions" in data
    assert "risk_factors" in data
