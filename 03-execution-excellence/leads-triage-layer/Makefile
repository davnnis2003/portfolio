.DEFAULT_GOAL := help
SHELL         := /bin/bash

API_HOST   ?= http://localhost:8000
LEADS_DIR  := data/new_leads
OUTPUT_DIR := output
LEAD_DIRS  := $(wildcard $(LEADS_DIR)/LEAD-*)

.PHONY: help serve health triage-rules triage clean

help:  ## Show this help
	@awk 'BEGIN{FS=":.*## "} /^[a-zA-Z_-]+:.*## /{printf "  %-18s%s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ── Server ────────────────────────────────────────────────────────────────────

serve:  ## Start the FastAPI server (blocking — open a new terminal to run triage)
	uv run uvicorn api.main:app --reload

health:  ## Check API server health
	@curl -sf $(API_HOST)/health | python3 -m json.tool

$(OUTPUT_DIR):
	@mkdir -p $@

# ── Triage ────────────────────────────────────────────────────────────────────

triage-rules: | $(OUTPUT_DIR)  ## Rule Engine only — no API required
	PYTHONPATH=src uv run python src/cli/run_triage.py

triage: | $(OUTPUT_DIR)  ## Full pipeline for all leads (API must be running)
	@echo "Running pipeline against $(API_HOST)"
	@echo ""
	@for dir in $(LEAD_DIRS); do \
		id=$$(basename $$dir); \
		out=$(OUTPUT_DIR)/$$id; \
		mkdir -p $$out; \
		echo "── $$id ────────────────────────────────────────"; \
		\
		printf "  [1/5] Interpretation › Rule Engine     "; \
		python3 -c "\
import json, sys; sys.path.insert(0, 'src'); \
from interpretation_layer.rule_engine import RuleEngine; \
d = json.load(open('$$dir/intake.json')); \
status, reasons = RuleEngine().evaluate(d); \
print(json.dumps({'rule_status': status, 'rule_reasons': reasons}, indent=2)); \
		" > $$out/01_rule_engine.json 2>/dev/null \
		&& echo "ok ($$(python3 -c "import json; print(json.load(open('$$out/01_rule_engine.json'))['rule_status'])"))" || echo "FAILED"; \
		\
		printf "  [2/5] Interpretation › LLM Parser      "; \
		python3 -c "\
import json; \
d = json.load(open('$$dir/intake.json')); \
d['_rule'] = json.load(open('$$out/01_rule_engine.json')); \
t = open('$$dir/transcript.md').read(); \
print(json.dumps({'intake_data': d, 'transcript_text': t})); \
		" | curl -sf -X POST $(API_HOST)/llm-parser/parse \
		  -H 'Content-Type: application/json' -d @- \
		| python3 -m json.tool > $$out/02_llm_parser.json 2>/dev/null \
		&& echo "ok ($$(python3 -c "import json; print(json.load(open('$$out/02_llm_parser.json')).get('rule_status', 'MISSING'))"))" || echo "FAILED"; \
		\
		status=$$(python3 -c "import json; print(json.load(open('$$out/01_rule_engine.json')).get('rule_status'))" 2>/dev/null); \
		if [ "$$status" = "DISQUALIFIED" ]; then \
			echo "  → Short-circuiting: Lead disqualified by rules. Skipping remaining steps."; \
			echo ""; \
			continue; \
		fi; \
		\
		printf "  [3/5] Memory   › Search                "; \
		python3 -c "\
import json; \
d = json.load(open('$$dir/intake.json')); \
f = d.get('fields', {}); \
t = open('$$dir/transcript.md').read(); \
print(json.dumps({'region': d['address']['region'], 'product': d['product'], \
  'building_year': f.get('building_year'), 'fassaden_typ': f.get('fassaden_typ'), \
  'transcript_text': t, 'top_k': 5})); \
		" | curl -sf -X POST $(API_HOST)/memory/search \
		  -H 'Content-Type: application/json' -d @- \
		> $$out/03_memory.json 2>/dev/null \
		&& echo "ok" || echo "FAILED"; \
		\
		printf "  [4/5] Decision › Engine                "; \
		python3 -c "\
import json; \
d = json.load(open('$$dir/intake.json')); \
d['_rule']   = json.load(open('$$out/01_rule_engine.json')); \
d['_llm']    = json.load(open('$$out/02_llm_parser.json')); \
d['_memory'] = json.load(open('$$out/03_memory.json')).get('stats', {}); \
t = open('$$dir/transcript.md').read(); \
print(json.dumps({'intake_data': d, 'transcript_text': t})); \
		" | curl -sf -X POST $(API_HOST)/decision/evaluate \
		  -H 'Content-Type: application/json' -d @- \
		> $$out/04_decision.json 2>/dev/null \
		&& echo "ok" || echo "FAILED"; \
		\
		printf "  [5/5] Decision › Field Briefing        "; \
		python3 -c "\
import json; \
d = json.load(open('$$dir/intake.json')); \
d['_decision'] = json.load(open('$$out/04_decision.json')); \
t = open('$$dir/transcript.md').read(); \
print(json.dumps({'intake_data': d, 'transcript_text': t})); \
		" | curl -sf -X POST $(API_HOST)/briefing/generate \
		  -H 'Content-Type: application/json' -d @- \
		> $$out/05_briefing.json 2>/dev/null \
		&& echo "ok" || echo "FAILED"; \
		\
		decision=$$(python3 -c "import json; print(json.load(open('$$out/04_decision.json')).get('decision','?'))" 2>/dev/null); \
		conf=$$(python3 -c "import json; print(str(json.load(open('$$out/04_decision.json')).get('confidence_score', 0)) + '/5')" 2>/dev/null); \
		echo "  → $$decision  ($$conf confidence)"; \
		echo ""; \
	done
	@uv run python src/cli/aggregate_results.py $(OUTPUT_DIR)

# ── Utilities ─────────────────────────────────────────────────────────────────

clean:  ## Remove all generated output files
	rm -rf $(OUTPUT_DIR)
