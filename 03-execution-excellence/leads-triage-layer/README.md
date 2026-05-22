# 🏠 ClimateTech Triage Layer

> **Quick Links:** [📄 Decision Log](docs/DECISION_LOG.md) | [🏗 Architecture Diagram](docs/ClimateTech_triage_layer.excalidraw) | [📋 Case Study](docs/JP%20BAI:%20Case%20Study.md)

Autonomous lead qualification for home insulation at scale. Built for the [JP BAI: Case Study](docs/JP%20BAI:%20Case%20Study.md), this system processes CRM data and call transcripts to automate the qualification, pricing, and briefing of new leads.

## 🚀 Quick Start

1. **Start the Infrastructure**
   ```bash
   docker compose up -d
   ```

2. **Start the API Server**
   ```bash
   make serve
   ```

3. **Run the Triage Pipeline** (in a new terminal)
   ```bash
   make triage
   ```

*The system is modular. You can test individual layers (see docs for examples):*
- **[Rule Engine](src/interpretation_layer/rule_engine/README.md)**: Deterministic qualification based on building rules (Step 1).
- **[LLM Parser](src/interpretation_layer/llm_parser/README.md)**: Detects contradictions between intake and transcript (Step 2).
- **[Memory Layer](src/memory_layer/README.md)**: Searches 1,000+ past projects for similarity (Step 3).
- **[Decision Engine](src/decision_layer/README.md)**: Synthesizes all signals into a triage decision (Step 4).
- **[Field Briefing](src/decision_layer/briefing/README.md)**: Generates actionable notes for sales reps (Step 5).

---

All 10 leads in `data/new_leads/` will be processed. Results are saved in the **[output/](output/)** directory.

### 📂 Results Structure

Each lead generates a dedicated folder containing the artifact of each pipeline stage:

- `01_rule_engine.json`: Deterministic qualification status and reasons.
- `02_llm_parser.json`: Extracted entities and cross-check contradictions.
- `03_memory.json`: Historical project similarity matches and stats.
- `04_decision.json`: Final triage decision and confidence reasoning.
- `05_briefing.json`: Actionable bullet points for the field sales rep.
- **`triage_results.json`**: An aggregated summary of all 10 lead results.

> [!IMPORTANT]
> **Ollama Cloud:** An `OLLAMA_API_KEY` is required in your environment (or `docker/.env`) for smooth, high-performance LLM inference. See [ollama.com/settings/keys](https://ollama.com/settings/keys) for details. The system will fall back to local Ollama if the key is missing.

---

## 🏗 System Architecture

The pipeline processes leads through three distinct layers:

1.  **Interpretation Layer**: A deterministic **[Rule Engine](src/interpretation_layer/rule_engine/README.md)** evaluates hard disqualifiers, followed by an **[LLM Parser](src/interpretation_layer/llm_parser/README.md)** that cross-checks the structured intake against the transcript to detect contradictions.
2.  **Memory Layer**: Uses retrieval-augmented generation (**[RAG](src/memory_layer/README.md)**) over 1,000 historical projects to find similar builds and surface past performance data.
3.  **Decision Layer**: Synthesizes all signals into a final **[Decision Engine](src/decision_layer/README.md)** outcome (`pitch`, `disqualify`, etc.) and generates actionable **[Field Briefings](src/decision_layer/briefing/README.md)** for sales reps.

---

## 🛠 Tech Stack

- **Python** (managed by `uv`)
- **FastAPI** (Backend API)
- **Ollama** (Cloud & Local LLM inference)
- **Docker** (Orchestration)

---

> [!TIP]
> **Testing:** To verify the system's integrity, run the full test suite with `uv run pytest tests/`.

> [!NOTE]
> **Data:** The `data/` directory contains the 1,000 past projects and 10 new leads provided as part of the original case study brief.

> [!NOTE]
> **Vibe Coding:** For details on the LLM-assisted development patterns used, see the **[AI Instructions](docs/AI_INSTRUCTIONS.md)**.

> [!CAUTION]
> **Legacy Code:** The **[src/legacy/](src/legacy/)** directory contains experimental prototypes (ML pipelines, database schemas) that were deliberately parked in favor of the current stateless, LLM-based architecture. See the **[Decision Log](docs/DECISION_LOG.md)** for the rationale.
