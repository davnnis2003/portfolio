# Memory Layer

Enables similarity search across past projects and provides aggregate performance statistics (close rate, issues, overruns) for historical cases.

## Usage

### 1. CLI
Search for similar past projects using a lead directory:
```bash
python src/cli/main.py memory --dir data/new_leads/LEAD-002
```

### 2. Backend API
Send a POST request with lead features and transcript to find similar historical projects:
```bash
curl -X POST http://localhost:8000/memory/search \
     -H "Content-Type: application/json" \
     -d '{
           "region": "NRW_SudNieder",
           "product": "fassade",
           "building_year": 1960,
           "transcript_text": "Customer has a bungalow built in 1960...",
           "top_k": 3
         }'
```

**Example Response:**
```json
{
  "query": {
    "region": "NRW_SudNieder",
    "product": "fassade",
    "building_year": 1960,
    "fassaden_typ": null,
    "transcript_text": "Customer has a bungalow built in 1960...",
    "top_k": 3
  },
  "similar_projects": [
    {
      "project_id": "PROJECT-00169",
      "region": "NRW_SudNieder",
      "product": "fassade",
      "building_type": "MFH",
      "building_year": 1960,
      "fassaden_typ": "naturstein",
      "mauerstarke_cm": 52.0,
      "has_hohlraum": true,
      "sales_call_summary": "Quick Call mit Frau Lange. Mehrfamilienhaus 4 Stockwerke BJ 1960 mit Natursteinfassade. Hohlraumd\u00e4mmung war gefragt, aber bei der Gr\u00f6\u00dfe des Geb\u00e4udes machen wir das nicht. Fernw\u00e4rme. Disqualifiziert.",
      "stage": "disqualified_phase1",
      "initial_quote_eur": null,
      "final_quote_eur": null,
      "on_site_issues": [],
      "customer_satisfaction": null
    },
    {
      "project_id": "PROJECT-00510",
      "region": "NRW_SudNieder",
      "product": "fassade",
      "building_type": "RH",
      "building_year": 1960,
      "fassaden_typ": "rotklinker",
      "mauerstarke_cm": null,
      "has_hohlraum": false,
      "sales_call_summary": "Gerade den ersten Call mit Frau Meier gehabt, sehr netter Kontakt! Sie wohnt in einem Reihenhaus Baujahr 1960 in NRW/s\u00fcdliches Niedersachsen, was sie selbst bewohnt. Ihr Hauptthema sind die hohen Heizkosten \u2013 sie hat noch eine \u00d6lheizung und das geht ihr wirklich auf den Keks, besonders in der aktuellen Zeit. Wir haben \u00fcber Fassadend\u00e4mmung gesprochen, speziell Kernd\u00e4mmung/Einblasd\u00e4mmung. Das Problem ist, dass ihre Fassade aus rotem Klinker besteht und sie leider keinen Hohlraum hat. Das war schnell klar, als wir das besprochen haben. Das hei\u00dft, Einblasd\u00e4mmung f\u00e4llt leider raus. Das haben wir im Gespr\u00e4ch auch direkt gekl\u00e4rt. Das ist nat\u00fcrlich schade, weil sie wirklich motiviert war, etwas an ihren Energiekosten zu \u00e4ndern. Sie wollte das eigentlich auch relativ bald angehen, so in den n\u00e4chsten 3-6 Monaten. Ich habe ihr jetzt erstmal gesagt, dass das mit der Einblasd\u00e4mmung nicht geht und wir da andere L\u00f6sungen finden m\u00fcssten, aber das ist ja nicht unser prim\u00e4res Business. Trotzdem, nice meeting her!",
      "stage": "qualified_declined",
      "initial_quote_eur": 1950.0,
      "final_quote_eur": 1950.0,
      "on_site_issues": [],
      "customer_satisfaction": null
    },
    {
      "project_id": "PROJECT-00789",
      "region": "NRW_SudNieder",
      "product": "fassade",
      "building_type": "EFH",
      "building_year": 1960,
      "fassaden_typ": "verputzt",
      "mauerstarke_cm": 28.0,
      "has_hohlraum": false,
      "sales_call_summary": "Gesprochen mit Frau Krause. Sucht nach Fassadend\u00e4mmung f\u00fcr ihr Haus von '60 in NRW. \u00d6lheizung und hohe Kosten nerven. Haus hat 28cm Putzfassade, aber leider keinen Hohlraum zum d\u00e4mmen. Einblasd\u00e4mmung nicht m\u00f6glich.",
      "stage": "qualified_lost",
      "initial_quote_eur": 3100.0,
      "final_quote_eur": 3100.0,
      "on_site_issues": [],
      "customer_satisfaction": null
    }
  ],
  "stats": {
    "total_similar": 3,
    "close_rate": 0.0,
    "avg_overrun_eur": 0.0,
    "common_issues": []
  }
```

**Hitting local lead files (LEAD-002):**
To search memory using a local lead's data via the API, you can use `jq` to build the payload:
```bash
# Example for LEAD-002
TRANSCRIPT=$(cat data/new_leads/LEAD-002/transcript.md)
INTAKE=$(cat data/new_leads/LEAD-002/intake.json)

curl -X POST http://localhost:8000/memory/search \
     -H "Content-Type: application/json" \
     -d "$(jq -n --arg t "$TRANSCRIPT" --argjson i "$INTAKE" \
       '{region: $i.address.region, product: $i.product, building_year: $i.fields.building_year, fassaden_typ: $i.fields.fassaden_typ, transcript_text: $t, top_k: 5}')"
```

---
*Note: The Memory layer uses Ollama embeddings for semantic similarity on project summaries. Ensure Ollama is running.*
