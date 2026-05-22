# ML Pipeline

Three sequential models predict the triage outcome for a lead. Each stage feeds its output into the next.

```
Lead features
     │
     ▼
 [1. Issues]  ──────────────────────────────────► has_issues_prob
     │                                                   │
     ▼                                                   ▼
 [2. Confidence]  ◄──────────────────── has_issues_prob  │
     │                                                   │
     ▼                                                   ▼
 [3. Triage]  ◄──────────────── has_issues_prob + confidence_score_pred
     │
     ▼
 triage_decision
```

---

## Stage 1 — Issues (`models/issues/`)

**What it predicts:** Binary flags indicating whether a lead has any problematic signals from the sales call.

| Model file | Target | Type |
|---|---|---|
| `model_has_issues.joblib` | `has_issues` | Binary classification |
| `model_has_scope_issue.joblib` | `has_scope_issue` | Binary classification |
| `model_has_time_issue.joblib` | `has_time_issue` | Binary classification |
| `preprocessor.joblib` | Shared preprocessor | `ColumnTransformer` |

**Input features:** `region`, `product`, `customer_segment`, `call_duration_min`, `building_year`, `has_hohlraum`, `heating_system`

**Key output:** `has_issues_prob` — probability of the lead having any issue, passed downstream.

**Training source:** `marts.project_insights`

---

## Stage 2 — Confidence (`models/confidence/`)

**What it predicts:** A confidence score from **1–5** reflecting how suitable the lead is for a pitch (based on call quality and lead characteristics).

| Model file | Target | Type |
|---|---|---|
| `model_confidence.joblib` | `confidence_score` (1–5) | Multiclass classification |
| `preprocessor.joblib` | Preprocessor | `ColumnTransformer` |

**Input features:** Stage 1 features + `has_issues_prob`

**Key output:** `confidence_score_pred` (integer 1–5), passed downstream. Scores ≤ 2 trigger an automatic `escalate` override in Stage 3.

**Training source:** `marts.confidence_training_data`

---

## Stage 3 — Triage (`models/triage/`)

**What it predicts:** The final triage decision for the lead.

| Possible decision | Meaning |
|---|---|
| `pitch` | Proceed with standard pitch |
| `pitch_with_flag` | Pitch with a noted concern |
| `pitch_with_cross_sell` | Pitch and propose additional product |
| `disqualify` | Lead does not qualify |
| `escalate` | Needs human review |

| Model file | Purpose |
|---|---|
| `model_triage.joblib` | Multiclass logistic regression |
| `preprocessor.joblib` | Numeric + categorical preprocessing |
| `vectorizer.joblib` | TF-IDF on `transcript_text` (100 features) |
| `classes.joblib` | Saved class label array |

**Input features:** Stage 1 + 2 features + `confidence_score_pred` + `transcript_text`

**Decision logic (in priority order):**
1. **Hard rules** — deterministic disqualification based on product/region/building constraints (e.g. wall thickness, building year, cellar conditions). Source: `docs/qualification_rules.md`.
2. **Rule overrides** — `confidence_score_pred ≤ 2` or model certainty `< 0.45` → `escalate`.
3. **ML model** — multiclass logistic regression over structured features + TF-IDF transcript.

**Training source:** `marts.project_insights`

---

## Preprocessing

All three stages share the same preprocessing pattern:

- **Numeric** (`call_duration_min`, `building_year`, …): median imputation → `StandardScaler`
- **Categorical** (`region`, `product`, `customer_segment`, …): constant imputation → `OneHotEncoder(handle_unknown='ignore')`
- **Text** (triage only): `TfidfVectorizer(max_features=100)`

Each preprocessor is fitted on training data and saved as `preprocessor.joblib` inside its model directory. Do **not** re-fit at inference time — call `.transform()` only.

---

## Running training

Training scripts read from the PostgreSQL database and write model artifacts back to `src/ml/models/`. Run in order:

```bash
uv run python src/ml/training/train_issues.py
uv run python src/ml/training/train_confidence.py
uv run python src/ml/training/train_triage.py
```

Requires a running Postgres instance (see `src/db/docker-compose.yml`) and `.env` with `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`.

## Running predictions via the API

The inference layer in `src/api/` loads all models once at startup and exposes them over HTTP — no database required at prediction time.

```bash
# Start the server
uv run uvicorn api.main:app --reload

# Run the full pipeline for a single lead
curl -X POST http://localhost:8000/predict/pipeline \
  -H "Content-Type: application/json" \
  -d '{"region": "NRW_SudNieder", "product": "fassade", ...}'
```

See `src/api/` for full request schemas and `src/cli/` for the CLI client.
