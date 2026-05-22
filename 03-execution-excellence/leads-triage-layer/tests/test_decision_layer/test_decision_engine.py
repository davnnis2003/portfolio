import pytest
from unittest.mock import MagicMock, patch
from decision_layer.decision_engine import DecisionEngine, TriageDecision
from interpretation_layer.llm_parser.parser import ParsedLead, EntityInfo, Contradiction, RiskFactor
from memory_layer.models import MemorySearchResult, AggregateStats, MemorySearchRequest

@pytest.fixture
def mock_components():
    with patch('decision_layer.decision_engine.RuleEngine') as mock_rule, \
         patch('decision_layer.decision_engine.LLMParser') as mock_llm, \
         patch('decision_layer.decision_engine.ProjectMemory') as mock_mem:
        
        yield mock_rule.return_value, mock_llm.return_value, mock_mem.return_value

def test_decision_engine_disqualify(mock_components):
    mock_rule, mock_llm, mock_mem = mock_components
    
    # Setup
    mock_rule.evaluate.return_value = ("DISQUALIFIED", ["Mauerwerk zu dünn"])
    mock_llm.parse.return_value = ParsedLead(
        entities=EntityInfo(),
        contradictions=[],
        risk_factors=[]
    )
    mock_mem.search.return_value = MemorySearchResult(
        query=MemorySearchRequest(),
        similar_projects=[],
        stats=AggregateStats(total_similar=0, close_rate=0.0, avg_overrun_eur=0.0, common_issues=[])
    )
    
    engine = DecisionEngine(memory_limit=0)
    result = engine.decide({"product": "fassade"}, "transcript")
    
    assert result.decision == TriageDecision.DISQUALIFY
    assert "Mauerwerk zu dünn" in result.reasoning

def test_decision_engine_pitch(mock_components):
    mock_rule, mock_llm, mock_mem = mock_components
    
    # Setup
    mock_rule.evaluate.return_value = ("QUALIFIED", [])
    mock_llm.parse.return_value = ParsedLead(
        entities=EntityInfo(),
        contradictions=[],
        risk_factors=[]
    )
    mock_mem.search.return_value = MemorySearchResult(
        query=MemorySearchRequest(),
        similar_projects=[],
        stats=AggregateStats(total_similar=10, close_rate=0.8, avg_overrun_eur=0.0, common_issues=[])
    )
    
    engine = DecisionEngine(memory_limit=0)
    result = engine.decide({"product": "fassade"}, "transcript")
    
    assert result.decision == TriageDecision.PITCH
    assert result.confidence_score == 5

def test_decision_engine_escalate_on_contradiction(mock_components):
    mock_rule, mock_llm, mock_mem = mock_components
    
    # Setup
    mock_rule.evaluate.return_value = ("QUALIFIED", [])
    mock_llm.parse.return_value = ParsedLead(
        entities=EntityInfo(),
        contradictions=[
            Contradiction(field="year", transcript_value="1950", intake_value="1980", reason="Diff")
        ] * 3, # 3 contradictions
        risk_factors=[]
    )
    mock_mem.search.return_value = MemorySearchResult(
        query=MemorySearchRequest(),
        similar_projects=[],
        stats=AggregateStats(total_similar=10, close_rate=0.5, avg_overrun_eur=0.0, common_issues=[])
    )
    
    engine = DecisionEngine(memory_limit=0)
    result = engine.decide({"product": "fassade"}, "transcript")
    
    assert result.decision == TriageDecision.ESCALATE
    assert "Detected 3 discrepancies" in result.reasoning[0]

def test_decision_engine_pitch_with_flag_low_memory(mock_components):
    mock_rule, mock_llm, mock_mem = mock_components
    
    # Setup
    mock_rule.evaluate.return_value = ("QUALIFIED", [])
    mock_llm.parse.return_value = ParsedLead(
        entities=EntityInfo(),
        contradictions=[],
        risk_factors=[RiskFactor(tag="ACCESS", description="Hard to reach", severity="MEDIUM")]
    )
    mock_mem.search.return_value = MemorySearchResult(
        query=MemorySearchRequest(),
        similar_projects=[],
        stats=AggregateStats(total_similar=10, close_rate=0.1, avg_overrun_eur=0.0, common_issues=[])
    )
    
    engine = DecisionEngine(memory_limit=0)
    result = engine.decide({"product": "fassade"}, "transcript")
    
    assert result.decision == TriageDecision.PITCH_WITH_FLAG
    assert any("Medium risk factors" in r for r in result.reasoning)
    assert any("Historical close rate is low" in r for r in result.reasoning)
