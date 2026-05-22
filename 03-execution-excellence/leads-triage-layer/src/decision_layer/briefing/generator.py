"""
Field Briefing Generator
========================
Consumes a :class:`DecisionOutput` from the Decision Engine and produces
4–6 structured, actionable bullet points for the field sales representative.

The generator does NOT re-parse the transcript or call the rule engine.
All analysis has already been done upstream; this module only synthesises
the results into a human-readable briefing.
"""
from __future__ import annotations

import os
import ollama
from typing import Optional

from decision_layer.decision_engine import DecisionOutput
from decision_layer.briefing.prompts import SYSTEM_PROMPT, BRIEFING_PROMPT
from utils.env_loader import init_env

# ---------------------------------------------------------------------------
# Pydantic model for a single briefing bullet
# ---------------------------------------------------------------------------
from pydantic import BaseModel
from typing import List


class BriefingBullet(BaseModel):
    """One actionable bullet point for the field rep."""
    label: str          # e.g. "CLARIFY", "PRICE CAREFULLY", "CONFIRM ON-SITE", ...
    text: str           # The instructional content of the bullet


class FieldBriefing(BaseModel):
    """Complete field briefing produced for a lead."""
    lead_id: Optional[str] = None
    decision: str
    confidence_pct: int
    bullets: List[BriefingBullet]
    raw_text: str        # The unprocessed LLM output, kept for debugging


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------

init_env()


def _format_contradictions(contradictions) -> str:
    if not contradictions:
        return "None"
    lines = []
    for c in contradictions:
        lines.append(
            f"  - {c.field}: transcript says '{c.transcript_value}', "
            f"intake says '{c.intake_value}' ({c.reason})"
        )
    return "\n".join(lines)


def _format_risk_factors(risk_factors) -> str:
    if not risk_factors:
        return "None"
    lines = []
    for r in risk_factors:
        lines.append(f"  - [{r.severity}] {r.tag}: {r.description}")
    return "\n".join(lines)


def _parse_bullets(raw_text: str) -> List[BriefingBullet]:
    """
    Parse the LLM output into structured BriefingBullet objects.

    Expects lines starting with "•" followed by a known label and a colon.
    Falls back to a single bullet if no structured lines are found.
    """
    known_labels = {
        "CLARIFY", "PRICE CAREFULLY", "CONFIRM ON-SITE",
        "CROSS-SELL", "FLAG", "NOTE"
    }
    bullets: List[BriefingBullet] = []

    for line in raw_text.splitlines():
        line = line.strip().lstrip("•-–").strip()
        if not line:
            continue

        # Try to split on the first ":"
        if ":" in line:
            label_candidate, _, rest = line.partition(":")
            label_upper = label_candidate.strip().upper()
            if label_upper in known_labels:
                bullets.append(BriefingBullet(label=label_upper, text=rest.strip()))
                continue

        # If the line looks like a bullet but has no recognised label, keep it
        if line:
            bullets.append(BriefingBullet(label="NOTE", text=line))

    # Clamp to 4–6 bullets
    if len(bullets) > 6:
        bullets = bullets[:6]

    return bullets


class BriefingGenerator:
    """
    Produces a :class:`FieldBriefing` from a :class:`DecisionOutput`.

    The generator talks to Ollama (local or cloud) using the structured
    BRIEFING_PROMPT – it never touches the raw transcript again.
    """

    def __init__(self, model_name: str = "gemma3:4b"):
        self.model_name = model_name
        api_key = os.getenv("OLLAMA_API_KEY")
        local_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

        if api_key:
            self.host = "https://ollama.com"
            headers = {"Authorization": f"Bearer {api_key}"}
            self.client = ollama.Client(host=self.host, headers=headers)
        else:
            self.host = local_host
            self.client = ollama.Client(host=self.host)

        try:
            self.client.list()
        except Exception as e:
            print(f"WARNING: Ollama not reachable at {self.host}: {e}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, decision_output: DecisionOutput) -> FieldBriefing:
        """
        Generate a field briefing from a :class:`DecisionOutput`.

        Parameters
        ----------
        decision_output:
            The fully-resolved output from :class:`DecisionEngine.decide()`.

        Returns
        -------
        FieldBriefing
            A structured briefing with 4–6 actionable bullet points.
        """
        prompt = self._build_prompt(decision_output)
        raw_text = self._call_llm(prompt)
        bullets = _parse_bullets(raw_text)

        # Guarantee at least 4 bullets even on minimal LLM output
        if len(bullets) < 4:
            bullets = self._fallback_bullets(decision_output)

        confidence_pct = round(decision_output.confidence_score / 5 * 100)

        return FieldBriefing(
            lead_id=decision_output.lead_id,
            decision=decision_output.decision.value,
            confidence_pct=confidence_pct,
            bullets=bullets,
            raw_text=raw_text,
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _build_prompt(self, d: DecisionOutput) -> str:
        entities = d.llm_analysis.entities
        stats = d.memory_stats

        return BRIEFING_PROMPT.format(
            decision=d.decision.value.upper(),
            confidence_pct=round(d.confidence_score / 5 * 100),
            house_type=entities.house_type or "unknown",
            insulation_type=entities.insulation_type or "unknown",
            cavity=entities.cavity or "unknown",
            access=entities.access or "unknown",
            region=entities.region or "unknown",
            constraints=entities.constraints or "none",
            n_contradictions=len(d.llm_analysis.contradictions),
            contradictions_block=_format_contradictions(d.llm_analysis.contradictions),
            risk_factors_block=_format_risk_factors(d.llm_analysis.risk_factors),
            total_similar=stats.total_similar,
            close_rate_pct=round(stats.close_rate * 100),
            avg_overrun=f"{stats.avg_overrun_eur:,.0f}",
            common_issues=", ".join(stats.common_issues) if stats.common_issues else "none recorded",
        )

    def _call_llm(self, prompt: str) -> str:
        try:
            response = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                system=SYSTEM_PROMPT,
                options={"temperature": 0.2},
            )
            return response["response"].strip()
        except Exception as e:
            return f"Error generating briefing with Ollama at {self.host}: {e}"

    def _fallback_bullets(self, d: DecisionOutput) -> List[BriefingBullet]:
        """
        Rule-based fallback used when the LLM output cannot be parsed into
        at least 4 bullets.  Guarantees a valid FieldBriefing is always returned.
        """
        bullets: List[BriefingBullet] = []
        entities = d.llm_analysis.entities
        stats = d.memory_stats

        # 1. Contradictions → CLARIFY
        if d.llm_analysis.contradictions:
            fields = ", ".join(c.field for c in d.llm_analysis.contradictions)
            bullets.append(BriefingBullet(
                label="CLARIFY",
                text=f"Discrepancies detected for: {fields}. Verify with the customer before quoting."
            ))

        # 2. High-risk factors → FLAG
        high_risks = [r for r in d.llm_analysis.risk_factors if r.severity == "HIGH"]
        if high_risks:
            tags = ", ".join(r.tag for r in high_risks)
            bullets.append(BriefingBullet(
                label="FLAG",
                text=f"High-severity risk factors present: {tags}. Review before committing to timeline."
            ))

        # 3. Cost overrun → PRICE CAREFULLY
        if stats.avg_overrun_eur > 0:
            bullets.append(BriefingBullet(
                label="PRICE CAREFULLY",
                text=(
                    f"Similar projects in this region show an average cost overrun of "
                    f"€{stats.avg_overrun_eur:,.0f}. Build in a buffer."
                )
            ))
        else:
            bullets.append(BriefingBullet(
                label="PRICE CAREFULLY",
                text="No historical overrun data available. Apply standard contingency to quote."
            ))

        # 4. Cavity confirmation → CONFIRM ON-SITE
        bullets.append(BriefingBullet(
            label="CONFIRM ON-SITE",
            text=(
                f"Verify cavity dimensions and wall composition on arrival "
                f"(reported: {entities.cavity or 'unknown'}). "
                "Drilling access must be confirmed before any commitment."
            )
        ))

        # 5. Low close rate → NOTE
        if stats.close_rate < 0.25 and stats.total_similar >= 3:
            bullets.append(BriefingBullet(
                label="NOTE",
                text=(
                    f"Historical close rate for similar leads is low "
                    f"({round(stats.close_rate * 100)}%). "
                    "Allocate visit time proportionally."
                )
            ))

        return bullets[:6]
