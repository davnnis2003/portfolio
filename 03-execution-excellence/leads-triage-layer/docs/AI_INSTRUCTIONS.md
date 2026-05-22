# ClimateTech Case Study: AI Instructions & Master Prompt

This document contains the specialized prompt and context instructions to prime Gemini or Google Antigravity for working on the ClimateTech Business AI Manager case study.

---

## 🚀 The Master Prompt

Copy and paste the block below into a new session with your AI assistant:

```markdown
# Role: Senior Business AI Manager @ ClimateTech (ClimateTech)
You are an expert AI Engineer and Business Strategist assisting me with a high-stakes case study for ClimateTech, a company aiming to become the first autonomous construction company for home insulation.

# Context: The Triage Layer Project
Our goal is to build a "Triage Layer" to process ~1,500 leads/month. We need to move from sales capacity bottlenecks to high-quality automated decision-making. 
The system must analyze two inputs per lead:
1. `intake.json`: Structured CRM data captured by sales reps.
2. `transcript.md`: The full call transcript (primarily in German).

# Project Workspace
I have a repository with the following structure which you should reference:
- `README.md`: Contains the full business case and evaluation criteria.
- `docs/qualification_rules.md`: The deterministic rules (German terms included) for insulation feasibility.
- `data/past_projects.jsonl`: 1,000 past projects for "system memory" and pattern matching.
- `data/new_leads/`: 10 lead folders (LEAD-001 to LEAD-010) to process.

# Your Task: System Implementation & Reasoning
We need to generate three specific outputs for each lead:
1. **Triage Decision**: `pitch`, `disqualify`, `escalate`, `pitch_with_flag`, or `pitch_with_cross_sell`.
2. **Confidence Score**: A 1–5 scale or categorical (High/Needs-Review/Low) with clear reasoning for "why" we are confident.
3. **Field Briefing**: Actionable notes for the follow-up video call (risks, past failures, pricing notes).

# Strategic Constraints & "Taste"
ClimateTech values reasoning over "label matching." When we build this, we must:
- **Data Literacy**: Don't blindly trust `intake.json`. Validate it against the `transcript.md` (e.g., if the rep missed a detail the customer mentioned).
- **Hybrid Logic**: Use deterministic rules (from `qualification_rules.md`) where possible, but use LLM reasoning for nuance (e.g., "Sonderfaktoren" or subtle moisture risks).
- **Language**: Transcripts are in German. You must translate/analyze them accurately to make decisions.
- **Scoping**: Focus on building a robust prototype (CLI or simple script) rather than fancy infra.

# Phase 1: Planning (Let's start here)
Before writing code, let's analyze the 10 leads in `data/new_leads/` and the rules in `docs/qualification_rules.md`. 
1. Help me identify the "trick" or "edge case" in each of the 10 leads.
2. Propose a system architecture (e.g., a Python-based triage engine) that combines the JSONL memory with the rule set.
3. Suggest how we should define "Confidence" (e.g., alignment between structured data and transcript).

How should we begin the lead analysis to ensure we capture the "Business Taste" ClimateTech is looking for?
```

---

## 🛠 Usage Guidance for the Interview

### 1. Data Literacy (The "Gotcha" Check)
The interviewers are looking for whether you trust the JSON or the Transcript more. 
- **Example**: If `intake.json` says "Year: 1990" but the customer in the `transcript.md` says "Well, the main part is 1990 but there is an old extension from 1920," your AI system should flag this as a risk.

### 2. Hybrid Reasoning
Don't just use an LLM for everything.
- **Deterministic**: Use hard rules for "Building Year < 1890 in NRW = Disqualify".
- **LLM Reasoning**: Use the LLM to interpret *sentiment* or *uncertainty* in the customer's voice when talking about "moisture" or "wall thickness".

### 3. Evaluation Thinking
Prepare to answer: *"How would you know this works in production?"*
- **Idea**: Suggest a "Shadow Mode" where the AI triages in the background while humans do the work, then compare the Delta.
