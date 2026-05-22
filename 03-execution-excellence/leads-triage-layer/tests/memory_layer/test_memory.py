import pytest
import numpy as np
from memory_layer.memory import ProjectMemory
from memory_layer.models import PastProject, MemorySearchRequest, AggregateStats

@pytest.fixture
def sample_project():
    return PastProject(
        project_id="PROJECT-TEST-001",
        region="NRW_SudNieder",
        product="fassade",
        building_type="EFH",
        building_year=1960,
        fassaden_typ="rotklinker",
        sales_call_summary="Test project summary.",
        stage="signed_installed",
        initial_quote_eur=5000,
        final_quote_eur=5500,
        on_site_issues=[{"category": "Weather"}, {"category": "Access"}]
    )

def test_calculate_stats(sample_project):
    memory = ProjectMemory()
    stats = memory.calculate_stats([sample_project])
    
    assert stats.total_similar == 1
    assert stats.close_rate == 1.0
    assert stats.avg_overrun_eur == 500.0
    assert "Weather" in stats.common_issues

def test_search_logic_basic(sample_project, mocker):
    memory = ProjectMemory()
    memory.projects = [sample_project]
    
    # Mock embedding to avoid network call
    mocker.patch.object(memory, '_get_embedding', return_value=np.array([0.1, 0.2, 0.3]))
    
    request = MemorySearchRequest(
        region="NRW_SudNieder",
        product="fassade",
        top_k=1
    )
    
    result = memory.search(request)
    assert len(result.similar_projects) == 1
    assert result.similar_projects[0]["project_id"] == "PROJECT-TEST-001"
    assert result.stats.total_similar == 1

def test_load_projects_nonexistent():
    memory = ProjectMemory(data_path="nonexistent.jsonl")
    memory.load_projects()
    assert len(memory.projects) == 0
