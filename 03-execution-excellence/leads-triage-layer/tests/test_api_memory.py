import pytest
from fastapi.testclient import TestClient
from api.main import app
import json

client = TestClient(app)

def test_memory_search_api(mocker):
    # Mock the ProjectMemory.search to avoid loading real data and calling Ollama
    mock_result = {
        "query": {"top_k": 5},
        "similar_projects": [
            {
                "project_id": "PROJECT-00001",
                "region": "NRW",
                "product": "fassade",
                "stage": "signed_installed",
                "sales_call_summary": "Summary",
                "building_type": "EFH"
            }
        ],
        "stats": {
            "total_similar": 1,
            "close_rate": 1.0,
            "avg_overrun_eur": 0.0,
            "common_issues": []
        }
    }
    
    # We need to mock the get_memory dependency or the ProjectMemory.search method
    mocker.patch("api.routers.memory.ProjectMemory.search", return_value=mocker.Mock(model_dump=lambda: mock_result))
    # Also mock load_projects to avoid actual file read
    mocker.patch("api.routers.memory.ProjectMemory.load_projects", return_value=None)

    response = client.post(
        "/memory/search",
        json={"region": "NRW", "product": "fassade", "top_k": 5}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["stats"]["total_similar"] == 1
    assert data["similar_projects"][0]["project_id"] == "PROJECT-00001"

def test_memory_index_api(mocker):
    mocker.patch("api.routers.memory.ProjectMemory.index_projects", return_value=None)
    mocker.patch("api.routers.memory.ProjectMemory.load_projects", return_value=None)

    response = client.post("/memory/index?limit=10")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
