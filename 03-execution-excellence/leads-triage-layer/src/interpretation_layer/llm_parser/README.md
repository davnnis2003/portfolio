# LLM Parser

Extracts structured insights (entities, contradictions, risks) from lead transcripts using LLM.

## Usage

### 1. CLI
Run the parser on a lead directory:
```bash
python src/cli/main.py parse --dir data/new_leads/LEAD-002
```

### 2. Backend API
Send a POST request with transcript and intake data:
```bash
curl -X POST http://localhost:8000/llm-parser/parse \
     -H "Content-Type: application/json" \
     -d '{
           "transcript_text": "Customer has a bungalow built in 2005. They are worried about the cold weather next week and need it done before winter.",
           "intake_data": {
             "lead_id": "L-54321",
             "building_year": 2000
           }
         }'
```

**Example Response:**
```json
{
  "entities": {
    "house_type": "Bungalow",
    "insulation_type": null,
    "cavity": null,
    "access": null,
    "region": null,
    "constraints": null
  },
  "contradictions": [
    {
      "field": "building_year",
      "transcript_value": "2005",
      "intake_value": "2000",
      "reason": "Discrepancy in building year. Transcript states 2005, while intake data indicates 2000."
    }
  ],
  "risk_factors": [
    {
      "tag": "Winterization",
      "description": "Customer concerned about cold weather and needs work completed before winter.",
      "severity": "MEDIUM"
    },
    {
      "tag": "Age of Property",
      "description": "Property built in 2005, potential for age-related issues.",
      "severity": "LOW"
    }
  ]
}%           
```

**Hitting local lead files (LEAD-002):**
To parse a local lead via the API, you can use `jq` to build the payload:
```bash
# Example for LEAD-002
TRANSCRIPT=$(cat data/new_leads/LEAD-002/transcript.md)
INTAKE=$(cat data/new_leads/LEAD-002/intake.json)

curl -X POST http://localhost:8000/llm-parser/parse \
     -H "Content-Type: application/json" \
     -d "$(jq -n --arg t "$TRANSCRIPT" --argjson i "$INTAKE" '{transcript_text: $t, intake_data: $i}')"
```

---
*Note: Ensure Ollama is running and `gemma3:4b` is pulled.*
