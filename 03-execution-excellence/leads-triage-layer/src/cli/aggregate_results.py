"""Aggregate per-lead pipeline outputs into output/triage_results.json."""
import json
import glob
import os
import re
import sys

output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"

KNOWN_LABELS = {"CLARIFY", "PRICE CAREFULLY", "CONFIRM ON-SITE", "CROSS-SELL", "FLAG", "NOTE"}

def _is_preamble(text: str) -> bool:
    """True for short LLM preamble lines that contain no actionable content."""
    t = text.lower().replace("’", "'").strip().rstrip(":")
    return "field briefing" in t and len(t) < 60

BOLD_LABEL_RE = re.compile(r"^\*{1,2}([A-Z][A-Z\s\-]+?)\*{0,2}\s*:\s*(.+)$", re.DOTALL)


def normalise_bullets(raw_bullets: list) -> list:
    """Fix two LLM output quirks:
    1. Label buried in text as **FLAG:** text → promote to label field.
    2. Preamble lines like "Here's your field briefing:" → drop.
    """
    clean = []
    for b in raw_bullets:
        text = b.get("text", "").strip()

        # Drop preamble lines
        if _is_preamble(text):
            continue

        label = b.get("label", "NOTE")

        # If label wasn't parsed (all came out as NOTE), try to extract from text
        if label == "NOTE":
            m = BOLD_LABEL_RE.match(text)
            if m:
                candidate = m.group(1).strip().upper()
                if candidate in KNOWN_LABELS:
                    label = candidate
                    text = m.group(2).strip()

        clean.append({"label": label, "text": text})
    return clean


def confidence_tier(score: int) -> str:
    if score >= 4:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


results = []
for lead_dir in sorted(glob.glob(f"{output_dir}/LEAD-*")):
    if not os.path.isdir(lead_dir):
        continue
    
    lead_id = os.path.basename(lead_dir)
    
    decision_file = os.path.join(lead_dir, "04_decision.json")
    rule_file = os.path.join(lead_dir, "01_rule_engine.json")
    briefing_file = os.path.join(lead_dir, "05_briefing.json")
    
    if os.path.exists(decision_file):
        d = json.load(open(decision_file))
        b = json.load(open(briefing_file)) if os.path.exists(briefing_file) else {}
        
        raw_score = d.get("confidence_score", 0)
        # Support legacy 0-1 float files: convert on the fly if not already 1-5
        if isinstance(raw_score, float) or raw_score > 5:
            score = max(1, min(5, round(raw_score * 5)))
        else:
            score = int(raw_score)
            
        raw_bullets = b.get("bullets", [])
        
        results.append({
            "lead_id": lead_id,
            "decision": d.get("decision"),
            "confidence_score": score,
            "confidence": confidence_tier(score),
            "rule_status": d.get("rule_status"),
            "rule_reasons": d.get("rule_reasons", []),
            "reasoning": d.get("reasoning", []),
            "field_briefing": normalise_bullets(raw_bullets),
        })
    elif os.path.exists(rule_file):
        # Lead likely disqualified or short-circuited
        r = json.load(open(rule_file))
        status = r.get("rule_status", "UNKNOWN")
        reasons = r.get("rule_reasons", [])
        
        if status == "DISQUALIFIED":
            results.append({
                "lead_id": lead_id,
                "decision": "disqualified",
                "confidence_score": 5,
                "confidence": "high",
                "rule_status": status,
                "rule_reasons": reasons,
                "reasoning": reasons,
                "field_briefing": []
            })

out_path = os.path.join(output_dir, "triage_results.json")
with open(out_path, "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Saved {out_path}  ({len(results)} leads)")
