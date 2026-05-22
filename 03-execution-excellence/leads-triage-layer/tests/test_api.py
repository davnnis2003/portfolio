import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from api.main import app
from decision_layer.briefing.generator import FieldBriefing, BriefingBullet

client = TestClient(app)

def test_generate_briefing_endpoint():
    payload = {
        "transcript_text": "Customer wants insulation.",
        "intake_data": {"lead_id": "LEAD-001"}
    }

    mock_briefing = FieldBriefing(
        lead_id="LEAD-001",
        decision="proceed",
        confidence_pct=80,
        bullets=[BriefingBullet(label="CONFIRM", text="Confirm insulation type on-site.")],
        raw_text="CONFIRM: Confirm insulation type on-site.",
    )

    with patch('decision_layer.briefing.generator.BriefingGenerator.generate') as mock_generate:
        mock_generate.return_value = mock_briefing

        response = client.post("/briefing/generate", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["decision"] == "proceed"
        assert data["confidence_pct"] == 80
        assert data["bullets"][0]["label"] == "CONFIRM"
        mock_generate.assert_called_once()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
