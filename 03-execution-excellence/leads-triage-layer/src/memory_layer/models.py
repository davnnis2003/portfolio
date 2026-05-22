from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PastProject(BaseModel):
    project_id: str
    region: str
    product: str
    building_type: str
    building_year: Optional[int] = None
    fassaden_typ: Optional[str] = None
    mauerstarke_cm: Optional[float] = None
    has_hohlraum: Optional[bool] = None
    sales_call_summary: str
    stage: str
    initial_quote_eur: Optional[float] = None
    final_quote_eur: Optional[float] = None
    on_site_issues: List[Dict[str, Any]] = Field(default_factory=list)
    customer_satisfaction: Optional[int] = None

class AggregateStats(BaseModel):
    total_similar: int
    close_rate: float
    avg_overrun_eur: float
    common_issues: List[str]

class MemorySearchRequest(BaseModel):
    region: Optional[str] = None
    product: Optional[str] = None
    building_year: Optional[int] = None
    fassaden_typ: Optional[str] = None
    transcript_text: Optional[str] = None
    top_k: int = 5

class MemorySearchResult(BaseModel):
    query: MemorySearchRequest
    similar_projects: List[Dict[str, Any]]
    stats: AggregateStats
