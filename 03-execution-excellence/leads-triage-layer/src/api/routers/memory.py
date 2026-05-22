from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from memory_layer.memory import ProjectMemory
from memory_layer.models import MemorySearchRequest, MemorySearchResult
import json
from fastapi.responses import Response

router = APIRouter(prefix="/memory", tags=["memory"])

# Singleton instance for memory (lazy loaded)
_memory_instance = None

def get_memory():
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = ProjectMemory()
        _memory_instance.load_projects()
        # For now, we don't auto-index all projects on startup to avoid slow boot
        # In a real app, this would be pre-computed or done in a background task
    return _memory_instance

@router.post("/search", response_model=MemorySearchResult)
def search_memory(request: MemorySearchRequest, memory: ProjectMemory = Depends(get_memory)):
    """
    Search for similar past projects and get aggregate statistics.
    """
    try:
        result = memory.search(request)
        # Return indented JSON for better readability in showcase
        return Response(
            content=json.dumps(result.model_dump(), indent=2),
            media_type="application/json"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/index")
def index_memory(limit: int = 100, memory: ProjectMemory = Depends(get_memory)):
    """
    Trigger manual indexing of projects (computing embeddings).
    """
    try:
        memory.index_projects(limit=limit)
        return {"status": "success", "message": f"Indexed up to {limit} projects"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
