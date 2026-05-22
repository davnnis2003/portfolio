import json
import os
from pathlib import Path
from interpretation_layer.rule_engine import RuleEngine

def run_triage():
    base_dir = Path("data/new_leads")
    engine = RuleEngine()
    
    results = []
    
    # Get all lead directories sorted by name
    lead_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir()])
    
    print(f"{'Lead ID':<10} | {'Status':<15} | {'Reasons'}")
    print("-" * 60)
    
    for lead_dir in lead_dirs:
        intake_path = lead_dir / "intake.json"
        if not intake_path.exists():
            continue
            
        with open(intake_path, "r") as f:
            intake_data = json.load(f)
            
        status, reasons = engine.evaluate(intake_data)
        lead_id = intake_data.get("lead_id", lead_dir.name)
        
        reasons_str = "; ".join(reasons) if reasons else "-"
        print(f"{lead_id:<10} | {status:<15} | {reasons_str}")
        
        results.append({
            "lead_id": lead_id,
            "status": status,
            "reasons": reasons
        })

    # Save summary to output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    with open(output_dir / "triage_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("-" * 60)
    print(f"Summary saved to output/triage_results.json")

if __name__ == "__main__":
    run_triage()
