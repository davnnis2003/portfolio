# Rule Engine

Deterministic lead qualification based on building constraints, regional requirements, and product feasibility.

## Usage

### 1. CLI
Run the rule engine locally on all leads:
```bash
make triage-rules
```

### 2. Backend API
Send a POST request with intake data:
```bash
curl -X POST http://localhost:8000/rule-engine/evaluate \
     -H "Content-Type: application/json" \
     -d '{
           "product": "fassade",
           "address": { "region": "NRW_SudNieder" },
           "fields": {
             "building_year": 1995,
             "mauerstarke_cm": 30
           }
         }'
```

Example Response:
```json
{
  "rule_status": "DISQUALIFIED",
  "rule_reasons": [
    "Region NRW_SudNieder: Baujahr 1995 > 1970 ohne 36.5cm Mauerstärke oder Klinker"
  ]
}
```

**Hitting local lead files (LEAD-001):**
```bash
# Example for LEAD-001
IN=$(cat data/new_leads/LEAD-001/intake.json)
curl -s -X POST http://localhost:8000/rule-engine/evaluate \
     -H "Content-Type: application/json" \
     -d "$(jq -n --argjson i "$IN" '{intake_data: $i}')" | jq .
```

---
*Note: This layer is strictly deterministic to ensure zero hallucination risk for hard disqualifiers.*
