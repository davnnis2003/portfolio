from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field
from interpretation_layer.rule_engine import RuleEngine
from interpretation_layer.llm_parser.parser import LLMParser, ParsedLead, RiskFactor, EntityInfo
from memory_layer.memory import ProjectMemory
from memory_layer.models import MemorySearchRequest, MemorySearchResult, AggregateStats
import enum

class TriageDecision(str, enum.Enum):
    PITCH = "pitch"
    DISQUALIFY = "disqualify"
    ESCALATE = "escalate"
    PITCH_WITH_FLAG = "pitch_with_flag"
    PITCH_WITH_CROSS_SELL = "pitch_with_cross_sell"

class DecisionOutput(BaseModel):
    lead_id: Optional[str] = None
    decision: TriageDecision
    confidence_score: int
    reasoning: List[str]
    rule_status: str
    rule_reasons: List[str]
    llm_analysis: ParsedLead
    memory_stats: AggregateStats

class DecisionEngine:
    def __init__(self, memory_limit: int = 50):
        self.rule_engine = RuleEngine()
        self.llm_parser = LLMParser()
        self.memory = ProjectMemory()
        self.memory.load_projects()
        # In production, indexing should be done once or in background
        # For this case study, we do a limited index
        self.memory.index_projects(limit=memory_limit)

    def decide(self, intake_data: Dict[str, Any], transcript_text: str) -> DecisionOutput:
        lead_id = intake_data.get("lead_id") or intake_data.get("id")
        
        # 1. Evaluate deterministic rules
        rule_status, rule_reasons = self.rule_engine.evaluate(intake_data)
        
        # Inject rule status for downstream LLM parsing consistency
        intake_data["_rule"] = {"rule_status": rule_status, "rule_reasons": rule_reasons}

        if rule_status == "DISQUALIFIED":
            # SHORT-CIRCUIT: Skip LLM and Memory if hard-disqualified by rules
            return DecisionOutput(
                lead_id=lead_id,
                decision=TriageDecision.DISQUALIFY,
                confidence_score=5,
                reasoning=rule_reasons,
                rule_status=rule_status,
                rule_reasons=rule_reasons,
                llm_analysis=ParsedLead(
                    entities=EntityInfo(),
                    contradictions=[],
                    risk_factors=[],
                    rule_status=rule_status,
                    rule_reasons=rule_reasons
                ),
                memory_stats=AggregateStats(
                    total_similar=0,
                    close_rate=0.0,
                    avg_overrun_eur=0.0,
                    common_issues=[]
                )
            )

        # 2. Analyze transcript and contradictions via LLM
        # Use pre-computed results if provided to ensure consistency with step 2
        precomputed_llm = intake_data.get("_llm")
        if precomputed_llm:
            llm_analysis = ParsedLead.model_validate(precomputed_llm)
        else:
            llm_analysis = self.llm_parser.parse(transcript_text, intake_data)
        
        # 3. Retrieve historical context from memory
        # Use pre-computed stats if provided to ensure consistency with step 3
        precomputed_memory = intake_data.get("_memory")
        if precomputed_memory:
            memory_stats = AggregateStats.model_validate(precomputed_memory)
            # Create a dummy result for synthesis (which only needs .stats)
            memory_result = MemorySearchResult(
                query=MemorySearchRequest(product=intake_data.get("product")),
                similar_projects=[],
                stats=memory_stats
            )
        else:
            search_req = MemorySearchRequest(
                product=intake_data.get("product"),
                region=intake_data.get("address", {}).get("region"),
                building_year=intake_data.get("fields", {}).get("building_year"),
                transcript_text=transcript_text,
                top_k=5
            )
            memory_result = self.memory.search(search_req)
            memory_stats = memory_result.stats
        
        # 4. Synthesize final decision and confidence
        decision, confidence, reasoning = self._synthesize(
            rule_status, rule_reasons, llm_analysis, memory_result
        )
        
        return DecisionOutput(
            lead_id=lead_id,
            decision=decision,
            confidence_score=confidence,
            reasoning=reasoning,
            rule_status=rule_status,
            rule_reasons=rule_reasons,
            llm_analysis=llm_analysis,
            memory_stats=memory_stats
        )

    def _synthesize(
        self,
        rule_status: str,
        rule_reasons: List[str],
        llm_analysis: ParsedLead,
        memory_result: MemorySearchResult
    ) -> Tuple[TriageDecision, int, List[str]]:
        
        reasoning = []
        
        # --- Confidence Score Components ---
        # 1. Consistency (30%): Contradictions subtract from here
        consistency_score = 1.0
        if llm_analysis.contradictions:
            num_contradictions = len(llm_analysis.contradictions)
            # Only penalize heavily if more than 2 actual contradictions
            penalty = 0.2 if num_contradictions <= 2 else 0.3
            consistency_score = max(0, 1.0 - (num_contradictions * penalty))
            reasoning.append(f"Detected {num_contradictions} discrepancies between intake and transcript.")
        
        # 2. Agreement (40%): Do rules and LLM and Memory agree?
        agreement_score = 0.5 # Default neutral
        
        # LLM Risk assessment
        high_risks = [r for r in llm_analysis.risk_factors if r.severity == "HIGH"]
        med_risks = [r for r in llm_analysis.risk_factors if r.severity == "MEDIUM"]
        
        # Memory evidence
        close_rate = memory_result.stats.close_rate
        
        if rule_status == "QUALIFIED":
            if not high_risks and close_rate > 0.4:
                agreement_score = 1.0
            elif high_risks or close_rate < 0.2:
                agreement_score = 0.4
        elif rule_status == "DISQUALIFIED":
            agreement_score = 1.0 # Rules are definitive
        
        # 3. Data Completeness (30%)
        # Check if critical fields exist
        critical_fields = ["product", "address", "fields"]
        present_fields = sum(1 for f in critical_fields if f in intake_data)
        completeness_score = present_fields / len(critical_fields)
        
        raw_confidence = (consistency_score * 0.3) + (agreement_score * 0.4) + (completeness_score * 0.3)
        # Map 0-1 float to 1-5 integer composite as documented
        final_confidence = max(1, min(5, round(raw_confidence * 5)))

        # --- Decision Logic ---

        # 0. Low-confidence override: anything ≤2 routes to escalate regardless of rules
        if final_confidence <= 2:
            reasoning.append("Confidence score ≤ 2 — routing to escalate for human review.")
            return TriageDecision.ESCALATE, final_confidence, reasoning

        # 1. Hard Disqualification
        if rule_status == "DISQUALIFIED":
            # Check for cross-sell potential (e.g. Fassade DQ'd but maybe OGD?)
            # For now, if DQ'd, we stay DQ'd unless Sonderfaktoren apply
            # We check if transcript mentions other products
            transcript_lower = llm_analysis.entities.house_type or "" # Just a proxy for now
            if any(term in rule_reasons[0].lower() for term in ["mauer", "fassade"]):
                # If fassade fails, check if basement or ogd was discussed
                # This is simplified: in reality we'd parse this specifically
                pass
            
            reasoning.extend(rule_reasons)
            return TriageDecision.DISQUALIFY, final_confidence, reasoning

        # 2. Escalation triggers
        if rule_status == "NEEDS_REVIEW":
            reasoning.append("Rule engine requires manual review (unknown product or edge case).")
            return TriageDecision.ESCALATE, final_confidence, reasoning
            
        if high_risks:
            reasoning.append(f"High risk factors detected: {', '.join([r.tag for r in high_risks])}")
            return TriageDecision.ESCALATE, final_confidence, reasoning
            
        if consistency_score < 0.5:
            reasoning.append("High level of contradictions between data sources.")
            return TriageDecision.ESCALATE, final_confidence, reasoning

        # 3. Pitch with Cross Sell
        # If lead is qualified for one but might benefit from others
        # (Simplified logic for showcase)
        if "cross-sell" in str(llm_analysis.risk_factors): # Hypothetical
             return TriageDecision.PITCH_WITH_CROSS_SELL, final_confidence, reasoning

        # 4. Pitch with Flag
        if med_risks or close_rate < 0.25:
            if med_risks:
                reasoning.append(f"Medium risk factors: {', '.join([r.tag for r in med_risks])}")
            if close_rate < 0.25:
                reasoning.append(f"Historical close rate is low ({close_rate:.1%}) for similar projects.")
            return TriageDecision.PITCH_WITH_FLAG, final_confidence, reasoning

        # 5. Pure Pitch
        reasoning.append("Qualified lead with high success likelihood and consistent data.")
        return TriageDecision.PITCH, final_confidence, reasoning
