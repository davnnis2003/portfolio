# Decision Engine

The **Decision Engine** is the orchestration layer that synthesizes deterministic rules, LLM-based transcript analysis, and historical project memory to make final lead triage decisions.

## Features

- **Deterministic Rules**: Evaluates leads against hard building constraints (wall thickness, building year, region).
- **LLM Synthesis**: Detects contradictions between intake and transcript, and flags high-severity risks.
- **Memory Integration**: Factors in historical success rates of similar past projects.
- **Confidence Scoring**: Weighted score based on data consistency, component agreement, and completeness.

## Usage

### 1. CLI
Evaluate a lead by pointing to its data directory:
```bash
python src/cli/main.py decision --dir data/new_leads/LEAD-002
```

### 2. Backend API
Send a POST request with transcript and intake data:
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

**Example Response (LEAD-002):**
```json
{
  "lead_id": "LEAD-002",
  "decision": "pitch",
  "confidence_score": 0.88,
  "reasoning": [
    "Qualified lead with high success likelihood and consistent data."
  ],
  "rule_status": "QUALIFIED",
  "rule_reasons": [],
  "llm_analysis": {
    "entities": {
      "house_type": "EFH",
      "insulation_type": "Fassadendämmung (Kerndämmung / Einblasdämmung)",
      "cavity": "6 cm",
      "region": "Hamburg/Schleswig-Holstein/nördliches Niedersachsen"
    },
    "contradictions": [
      {
        "field": "building_year",
        "transcript_value": "1960",
        "intake_value": "1960",
        "reason": "No discrepancy"
      }
    ],
    "risk_factors": [
      {
        "tag": "High_Cost",
        "description": "Customer expresses concern about cost and guarantees.",
        "severity": "MEDIUM"
      },
      {
        "tag": "Complexity_Permitting",
        "description": "Customer indicates difficulty understanding funding options.",
        "severity": "MEDIUM"
      }
    ]
  },
  "memory_stats": {
    "total_similar": 5,
    "close_rate": 0.0,
    "avg_overrun_eur": 0.0,
    "common_issues": []
  }
}
```

```bash
# Example using real lead LEAD-002
TRANSCRIPT=$(cat data/new_leads/LEAD-002/transcript.md)
INTAKE=$(cat data/new_leads/LEAD-002/intake.json)

curl -X POST http://localhost:8000/decision/evaluate \
     -H "Content-Type: application/json" \
     -d "$(jq -n --arg t "$TRANSCRIPT" --argjson i "$INTAKE" '{transcript_text: $t, intake_data: $i}')"
```

## Data Context

The Decision Engine leverages two primary data sources to inform its logic:

1.  **Intake & Transcripts (`data/new_leads/`)**: The system compares the structured intake data against the unstructured call transcripts to find contradictions and extract building features.
2.  **Historical Projects (`data/past_projects.jsonl`)**: The Memory Layer performs a similarity search against 1,000+ past projects. It calculates the **Historical Success Rate** (close rate) and identifies **Common Issues** encountered in similar building types and regions.

## Decision Categories

- **PITCH**: High confidence, low risk, high historical success.
- **PITCH_WITH_FLAG**: Manageable risks or low historical close rate detected.
- **ESCALATE**: High risk factors or significant data contradictions found.
- **DISQUALIFY**: Hard rule failure (e.g., wall thickness incompatible).
- **PITCH_WITH_CROSS_SELL**: Primary product disqualified but building suitable for alternative services.

---
*Note: Ensure Ollama is running and the necessary models (`gemma3:4b`, `nomic-embed-text`) are available.*
