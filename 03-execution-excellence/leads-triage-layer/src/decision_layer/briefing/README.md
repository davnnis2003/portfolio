# Field Briefing Generator

Produces **4–6 structured, actionable bullet points** for field sales representatives, synthesised from the Decision Engine's output (extracted entities, rule results, memory stats, and triage decision).

The generator does **not** re-parse the raw transcript — all analysis has already been done upstream by the Decision Engine.

## Output Bullet Labels

| Label | Purpose |
|---|---|
| `CLARIFY` | Something the rep must confirm with the customer |
| `PRICE CAREFULLY` | A cost or margin risk to watch when quoting |
| `CONFIRM ON-SITE` | Something that must be physically verified during the visit |
| `CROSS-SELL` | An additional product or service to propose (when relevant) |
| `FLAG` | An issue that may require escalation or senior review |
| `NOTE` | Any other important context |

## Usage

### 1. Backend API
Send a POST request with the same body as `/decision/evaluate`:
```bash
curl -X POST http://localhost:8000/decision/evaluate \
     -H "Content-Type: application/json" \
     -d '{
           "transcript_text": "Customer has a bungalow built in 1965. They want insulation for the facade.",
           "intake_data": {
             "lead_id": "L-999",
             "product": "fassade",
             "fields": {
               "building_year": 1965,
               "mauerstarke_cm": 30
             },
             "address": {
               "region": "NRW_SudNieder"
             }
           }
         }'
```

**Example Response:**
```json
{
  "lead_id": "L-999",
  "decision": "pitch_with_flag",
  "confidence_score": 0.76,
  "reasoning": [
    "Medium risk factors: Age of Building",
    "Historical close rate is low (0.0%) for similar projects."
  ],
  "rule_status": "QUALIFIED",
  "rule_reasons": [],
  "llm_analysis": {
    "entities": {
      "house_type": "Bungalow",
      "insulation_type": "Facade insulation",
      "cavity": "Present (implied by facade insulation request)",
      "access": "Not specified",
      "region": "NRW_SudNieder",
      "constraints": "None specified"
    },
    "contradictions": [],
    "risk_factors": [
      {
        "tag": "Age of Building",
        "description": "Building constructed in 1965, potential for issues related to older construction techniques and materials.",
        "severity": "MEDIUM"
      },
      {
        "tag": "Cavity Size",
        "description": "Cavity measurement of 30cm may be insufficient for optimal insulation performance, depending on the chosen insulation material and climate.",
        "severity": "LOW"
      }
    ]
  },
  "memory_stats": {
    "total_similar": 5,
    "close_rate": 0.0,
    "avg_overrun_eur": 0.0,
    "common_issues": []
  }
```


```bash
TRANSCRIPT=$(cat data/new_leads/LEAD-002/transcript.md)
INTAKE=$(cat data/new_leads/LEAD-002/intake.json)

curl -s -X POST http://localhost:8000/briefing/generate \
     -H "Content-Type: application/json" \
     -d "$(jq -n --arg t "$TRANSCRIPT" --argjson i "$INTAKE" '{transcript_text: $t, intake_data: $i}')" \
  | jq .
```

## Fallback Behaviour

If the LLM returns an unparseable response, the generator automatically falls back to a **deterministic rule-based briefing** derived directly from the Decision Engine output. A valid `FieldBriefing` with 4–6 bullets is always returned.

---
*Note: Ensure Ollama is running and `gemma3:4b` is pulled.*
