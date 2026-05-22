import pytest
from unittest.mock import MagicMock, patch
from interpretation_layer.llm_parser.parser import LLMParser, ParsedLead

@pytest.fixture
def mock_ollama():
    with patch('ollama.Client') as mock:
        yield mock

@pytest.fixture(autouse=True)
def no_env_vars():
    """Ensure tests don't pick up local OLLAMA_API_KEY."""
    with patch('os.getenv') as mock_getenv:
        def side_effect(key, default=None):
            if key == "OLLAMA_API_KEY":
                return None
            if key == "OLLAMA_HOST":
                return "http://localhost:11434"
            return default
        mock_getenv.side_effect = side_effect
        yield

def test_parser_init(mock_ollama):
    parser = LLMParser(model_name="test-model")
    assert parser.model_name == "test-model"
    assert "localhost:11434" in parser.host

def test_parse_success(mock_ollama):
    # Mock response from Ollama (Chat API)
    mock_client_instance = mock_ollama.return_value
    mock_client_instance.chat.return_value = {
        'message': {
            'content': '{"entities": {"house_type": "EFH", "insulation_type": "Einblas", "cavity": "5cm", "access": "Good", "region": "North", "constraints": "None"}, "contradictions": [], "risk_factors": [{"tag": "Weather", "description": "Cold", "severity": "LOW"}]}'
        }
    }

    parser = LLMParser()
    transcript = "Transcript text"
    intake = {"lead_id": "123", "region": "North"}
    
    result = parser.parse(transcript, intake)
    
    assert isinstance(result, ParsedLead)
    assert result.entities.house_type == "EFH"
    assert len(result.risk_factors) == 1
    assert result.risk_factors[0].tag == "Weather"

def test_parse_invalid_json(mock_ollama):
    mock_client_instance = mock_ollama.return_value
    mock_client_instance.chat.return_value = {
        'message': {
            'content': 'Invalid JSON'
        }
    }

    parser = LLMParser()
    with pytest.raises(Exception):
        parser.parse("transcript", {})
