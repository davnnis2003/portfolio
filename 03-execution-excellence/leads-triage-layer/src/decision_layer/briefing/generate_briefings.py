import os
import sys
import json
from pathlib import Path

# Add src to path - it's three levels up from this file's location
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root / "src"))

from decision_layer.decision_engine import DecisionEngine
from decision_layer.briefing.generator import BriefingGenerator

def main():
    data_dir = project_root / "data" / "new_leads"
    output_dir = project_root / "output"
    
    if not data_dir.exists():
        print(f"Error: {data_dir} does not exist.")
        return

    engine = DecisionEngine()
    generator = BriefingGenerator()
    
    lead_dirs = sorted([d for d in data_dir.iterdir() if d.is_dir()])
    
    for lead_dir in lead_dirs:
        lead_id = lead_dir.name
        print(f"Processing {lead_id}...")
        
        intake_path = lead_dir / "intake.json"
        transcript_path = lead_dir / "transcript.md"
        
        if not intake_path.exists() or not transcript_path.exists():
            print(f"  Missing intake or transcript for {lead_id}, skipping.")
            continue
            
        with open(intake_path, "r") as f:
            intake_data = json.load(f)
        with open(transcript_path, "r") as f:
            transcript_text = f.read()
            
        # 1. Run Decision Engine
        decision_output = engine.decide(intake_data, transcript_text)
        
        # 2. Generate Briefing
        briefing = generator.generate(decision_output)
        
        # 3. Save Output
        lead_output_dir = output_dir / lead_id
        lead_output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(lead_output_dir / "05_briefing.json", "w") as f:
            json.dump(briefing.model_dump(), f, indent=2, ensure_ascii=False)
            
        print(f"  Done. Saved to {lead_output_dir}/05_briefing.json")

if __name__ == "__main__":
    main()
