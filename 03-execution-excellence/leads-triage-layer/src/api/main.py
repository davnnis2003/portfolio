from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI

from legacy.model_loader import get_models
from api.routers import briefing, llm_parser, memory, decision, rule_engine
# Re-importing individually to ensure names are available if package loading is weird
from api.routers.briefing import router as briefing_router
from api.routers.llm_parser import router as llm_parser_router
from api.routers.memory import router as memory_router
from api.routers.decision import router as decision_router
from api.routers.rule_engine import router as rule_engine_router
from legacy.confidence import predict_confidence, router as confidence_router
from legacy.issues import predict_issues, router as issues_router
from legacy.triage import predict_triage, router as triage_router
from api.schemas import LeadInput, PipelinePrediction

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Warm up models
    get_models()
    yield
    # Shutdown: Clean up (if needed)

app = FastAPI(
    title="ClimateTech Lead Triage API",
    description="Serves ML predictions for lead triage, confidence scoring, and issue detection.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(issues_router)
app.include_router(confidence_router)
app.include_router(triage_router)
app.include_router(briefing_router)
app.include_router(llm_parser_router)
app.include_router(memory_router)
app.include_router(decision_router)
app.include_router(rule_engine_router)



@app.post("/predict/pipeline", response_model=PipelinePrediction, tags=["pipeline"])
def predict_pipeline(lead: LeadInput) -> PipelinePrediction:
    """Run the full issues → confidence → triage pipeline in one call."""
    issues_result = predict_issues(lead)

    lead_with_issues = lead.model_copy(
        update={"has_issues_prob": issues_result.has_issues_prob}
    )
    confidence_result = predict_confidence(lead_with_issues)

    lead_with_all = lead_with_issues.model_copy(
        update={"confidence_score_pred": float(confidence_result.confidence_score_pred)}
    )
    triage_result = predict_triage(lead_with_all)

    return PipelinePrediction(
        lead_id=lead.lead_id,
        issues=issues_result,
        confidence=confidence_result,
        triage=triage_result,
    )


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}
