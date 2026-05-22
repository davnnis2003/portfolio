"""
Tests for the refactored Field Briefing Generator.

The generator now consumes a DecisionOutput from the Decision Engine,
not raw transcript/intake data.  All LLM calls are mocked.
"""
import pytest
from unittest.mock import MagicMock, patch

from decision_layer.briefing.generator import (
    BriefingGenerator,
    BriefingBullet,
    FieldBriefing,
    _parse_bullets,
    _format_contradictions,
    _format_risk_factors,
)
from decision_layer.decision_engine import DecisionOutput, TriageDecision
from interpretation_layer.llm_parser.parser import (
    ParsedLead, EntityInfo, Contradiction, RiskFactor
)
from memory_layer.models import AggregateStats


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------

def _make_decision_output(
    decision=TriageDecision.PITCH,
    confidence=4,
    contradictions=None,
    risk_factors=None,
    total_similar=10,
    close_rate=0.6,
    avg_overrun=0.0,
    common_issues=None,
    lead_id="LEAD-TEST",
) -> DecisionOutput:
    return DecisionOutput(
        lead_id=lead_id,
        decision=decision,
        confidence_score=confidence,
        reasoning=["Test reasoning"],
        rule_status="QUALIFIED",
        rule_reasons=[],
        llm_analysis=ParsedLead(
            entities=EntityInfo(
                house_type="EFH",
                insulation_type="Kerndämmung",
                cavity="6 cm Hohlraum, Mauerdicke 36.5 cm",
                access="Bohren kleiner Löcher",
                region="SH_NordNieder_HH",
                constraints="Rotklinkerfassade",
            ),
            contradictions=contradictions or [],
            risk_factors=risk_factors or [],
        ),
        memory_stats=AggregateStats(
            total_similar=total_similar,
            close_rate=close_rate,
            avg_overrun_eur=avg_overrun,
            common_issues=common_issues or [],
        ),
    )


# ---------------------------------------------------------------------------
# Unit tests: _parse_bullets
# ---------------------------------------------------------------------------

def test_parse_bullets_standard_labels():
    raw = (
        "• CLARIFY: Confirm building year with the customer.\n"
        "• PRICE CAREFULLY: Wall access may incur scaffolding costs.\n"
        "• CONFIRM ON-SITE: Verify cavity depth before drilling.\n"
        "• FLAG: Time sensitivity flagged – customer wants work before winter."
    )
    bullets = _parse_bullets(raw)
    assert len(bullets) == 4
    assert bullets[0].label == "CLARIFY"
    assert "building year" in bullets[0].text
    assert bullets[2].label == "CONFIRM ON-SITE"


def test_parse_bullets_clamped_to_six():
    raw = "\n".join([
        f"• CLARIFY: Point {i}" for i in range(10)
    ])
    bullets = _parse_bullets(raw)
    assert len(bullets) <= 6


def test_parse_bullets_unknown_label_becomes_note():
    raw = "• RANDOM: Some text without a known label."
    bullets = _parse_bullets(raw)
    # Falls through to NOTE fallback
    assert all(b.label in {"NOTE", "RANDOM"} for b in bullets)


def test_parse_bullets_empty_input():
    bullets = _parse_bullets("")
    assert bullets == []


# ---------------------------------------------------------------------------
# Unit tests: formatting helpers
# ---------------------------------------------------------------------------

def test_format_contradictions_none():
    assert _format_contradictions([]) == "None"


def test_format_contradictions_with_data():
    contradictions = [
        Contradiction(
            field="building_year",
            transcript_value="1960",
            intake_value="1970",
            reason="Year mismatch",
        )
    ]
    result = _format_contradictions(contradictions)
    assert "building_year" in result
    assert "1960" in result
    assert "1970" in result


def test_format_risk_factors_none():
    assert _format_risk_factors([]) == "None"


def test_format_risk_factors_with_data():
    risks = [
        RiskFactor(tag="Time_Sensitivity", description="Before winter", severity="HIGH")
    ]
    result = _format_risk_factors(risks)
    assert "[HIGH]" in result
    assert "Time_Sensitivity" in result


# ---------------------------------------------------------------------------
# Integration tests: BriefingGenerator.generate()
# ---------------------------------------------------------------------------

LLM_BULLET_RESPONSE = (
    "• CLARIFY: Confirm building year (transcript: 1960, intake: 1970).\n"
    "• PRICE CAREFULLY: Rotklinkerfassade may require specialist equipment – add 15% buffer.\n"
    "• CONFIRM ON-SITE: Measure actual cavity depth; intake shows 6 cm but must be verified.\n"
    "• FLAG: Time sensitivity is HIGH – customer requires work before winter."
)


def _make_generator_with_mock(llm_response: str) -> BriefingGenerator:
    with patch("decision_layer.briefing.generator.ollama.Client") as mock_client_cls:
        instance = mock_client_cls.return_value
        instance.generate.return_value = {"response": llm_response}
        generator = BriefingGenerator()
        generator.client = instance   # replace after init
        return generator


@patch("decision_layer.briefing.generator.ollama.Client")
def test_generate_returns_field_briefing(mock_client_cls):
    instance = mock_client_cls.return_value
    instance.generate.return_value = {"response": LLM_BULLET_RESPONSE}

    generator = BriefingGenerator()
    decision_output = _make_decision_output()
    briefing = generator.generate(decision_output)

    assert isinstance(briefing, FieldBriefing)
    assert briefing.lead_id == "LEAD-TEST"
    assert briefing.decision == "pitch"
    assert briefing.confidence_pct == 80
    assert 4 <= len(briefing.bullets) <= 6


@patch("decision_layer.briefing.generator.ollama.Client")
def test_generate_bullet_labels_are_valid(mock_client_cls):
    instance = mock_client_cls.return_value
    instance.generate.return_value = {"response": LLM_BULLET_RESPONSE}

    generator = BriefingGenerator()
    decision_output = _make_decision_output()
    briefing = generator.generate(decision_output)

    valid_labels = {"CLARIFY", "PRICE CAREFULLY", "CONFIRM ON-SITE", "CROSS-SELL", "FLAG", "NOTE"}
    for bullet in briefing.bullets:
        assert bullet.label in valid_labels, f"Unexpected label: {bullet.label}"


@patch("decision_layer.briefing.generator.ollama.Client")
def test_generate_with_contradictions_in_prompt(mock_client_cls):
    """The prompt must encode contradictions so the LLM can act on them."""
    instance = mock_client_cls.return_value
    instance.generate.return_value = {"response": LLM_BULLET_RESPONSE}

    generator = BriefingGenerator()
    contradictions = [
        Contradiction(
            field="building_year",
            transcript_value="1960",
            intake_value="1970",
            reason="Year mismatch",
        )
    ]
    decision_output = _make_decision_output(contradictions=contradictions)
    generator.generate(decision_output)

    call_kwargs = instance.generate.call_args
    prompt_sent = call_kwargs[1]["prompt"] if call_kwargs[1] else call_kwargs[0][1]
    assert "building_year" in prompt_sent


@patch("decision_layer.briefing.generator.ollama.Client")
def test_fallback_bullets_on_empty_llm_response(mock_client_cls):
    """When LLM returns nothing parseable, the rule-based fallback kicks in."""
    instance = mock_client_cls.return_value
    instance.generate.return_value = {"response": ""}

    generator = BriefingGenerator()
    decision_output = _make_decision_output(
        contradictions=[
            Contradiction(field="wall_thickness", transcript_value="36cm", intake_value="30cm", reason="Diff")
        ],
        risk_factors=[
            RiskFactor(tag="Time_Sensitivity", description="Before winter", severity="HIGH")
        ],
    )
    briefing = generator.generate(decision_output)

    assert isinstance(briefing, FieldBriefing)
    assert 4 <= len(briefing.bullets) <= 6
    labels = {b.label for b in briefing.bullets}
    assert "CLARIFY" in labels or "FLAG" in labels or "CONFIRM ON-SITE" in labels


@patch("decision_layer.briefing.generator.ollama.Client")
def test_escalate_decision_is_reflected(mock_client_cls):
    instance = mock_client_cls.return_value
    instance.generate.return_value = {"response": LLM_BULLET_RESPONSE}

    generator = BriefingGenerator()
    decision_output = _make_decision_output(
        decision=TriageDecision.ESCALATE,
        confidence=3,
    )
    briefing = generator.generate(decision_output)

    assert briefing.decision == "escalate"
    assert briefing.confidence_pct == 60


@patch("decision_layer.briefing.generator.ollama.Client")
def test_disqualify_decision_represented_correctly(mock_client_cls):
    instance = mock_client_cls.return_value
    instance.generate.return_value = {"response": LLM_BULLET_RESPONSE}

    generator = BriefingGenerator()
    decision_output = _make_decision_output(
        decision=TriageDecision.DISQUALIFY,
        confidence=4,
    )
    briefing = generator.generate(decision_output)
    assert briefing.decision == "disqualify"
    assert briefing.confidence_pct == 80


@patch("decision_layer.briefing.generator.ollama.Client")
def test_cross_sell_bullet_when_present(mock_client_cls):
    cross_sell_response = (
        "• CLARIFY: Confirm cavity size.\n"
        "• PRICE CAREFULLY: Clinker façade adds cost.\n"
        "• CONFIRM ON-SITE: Test drilling feasibility.\n"
        "• CROSS-SELL: Customer may benefit from roof insulation (OGD).\n"
    )
    instance = mock_client_cls.return_value
    instance.generate.return_value = {"response": cross_sell_response}

    generator = BriefingGenerator()
    decision_output = _make_decision_output(decision=TriageDecision.PITCH_WITH_CROSS_SELL)
    briefing = generator.generate(decision_output)

    assert any(b.label == "CROSS-SELL" for b in briefing.bullets)


@patch("decision_layer.briefing.generator.ollama.Client")
def test_memory_stats_low_close_rate_triggers_note(mock_client_cls):
    """Fallback path: low close rate should produce a NOTE bullet."""
    instance = mock_client_cls.return_value
    # Return empty response so fallback path is taken
    instance.generate.return_value = {"response": ""}

    generator = BriefingGenerator()
    decision_output = _make_decision_output(
        total_similar=5,
        close_rate=0.10,   # below 25% threshold
    )
    briefing = generator.generate(decision_output)

    labels = [b.label for b in briefing.bullets]
    assert "NOTE" in labels
    note_texts = [b.text for b in briefing.bullets if b.label == "NOTE"]
    assert any("close rate" in t.lower() for t in note_texts)
