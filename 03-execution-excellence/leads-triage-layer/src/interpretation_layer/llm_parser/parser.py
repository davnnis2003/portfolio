import os
import json
import ollama
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from .prompts import SYSTEM_PROMPT, PARSER_PROMPT
from utils.env_loader import init_env

# Initialize environment variables
init_env()

class EntityInfo(BaseModel):
    house_type: Optional[str] = None
    insulation_type: Optional[str] = None
    cavity: Optional[str] = None
    access: Optional[str] = None
    region: Optional[str] = None
    constraints: Optional[str] = None

class Contradiction(BaseModel):
    field: str
    transcript_value: str
    intake_value: str
    reason: str

class RiskFactor(BaseModel):
    tag: str
    description: str
    severity: str # LOW, MEDIUM, HIGH

class ParsedLead(BaseModel):
    entities: EntityInfo
    contradictions: List[Contradiction] = Field(default_factory=list)
    risk_factors: List[RiskFactor] = Field(default_factory=list)
    rule_status: Optional[str] = None
    rule_reasons: List[str] = Field(default_factory=list)

def extract_json(text: str) -> str:
    """
    Extracts the first JSON object from a string, handling markdown code blocks.
    """
    # Remove markdown code blocks if present
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    
    return text.strip()


class LLMParser:
    def __init__(self, model_name: str = "gemma3:4b"):
        self.model_name = model_name
        
        # Load API key and host
        api_key = os.getenv("OLLAMA_API_KEY")
        local_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        if api_key:
            # Use Ollama Cloud
            self.host = "https://ollama.com"
            headers = {"Authorization": f"Bearer {api_key}"}
            print(f"INFO: Using Ollama Cloud with model {self.model_name}")
            self.client = ollama.Client(host=self.host, headers=headers)
        else:
            # Fallback to local Ollama
            self.host = local_host
            print(f"INFO: Using local Ollama at {self.host} with model {self.model_name}")
            self.client = ollama.Client(host=self.host)


    def parse(self, transcript_text: str, intake_data: Dict[str, Any]) -> ParsedLead:
        """
        Parses a transcript and intake data using the LLM.
        """
        intake_json = json.dumps(intake_data, indent=2)
        prompt = PARSER_PROMPT.format(
            transcript=transcript_text,
            intake=intake_json
        )

        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat(
                model=self.model_name,
                messages=messages,
                format="json",
                options={
                    "temperature": 0.1,
                }
            )
            
            raw_response = response['message']['content']
            
            if not raw_response or raw_response.strip() == "":
                raise ValueError("Empty response from LLM")

            # Extract JSON from potential markdown wrapping
            json_str = extract_json(raw_response)
            data = json.loads(json_str)

            
            # Ensure required fields are present
            if "entities" not in data:
                data["entities"] = {}
            if "contradictions" not in data:
                data["contradictions"] = []
            if "risk_factors" not in data:
                data["risk_factors"] = []

            # Filter out "phantom contradictions" where LLM says there's no discrepancy
            data["contradictions"] = [
                c for c in data["contradictions"]
                if "match" not in c.get("reason", "").lower() 
                and "no discrepancy" not in c.get("reason", "").lower()
                and "no difference" not in c.get("reason", "").lower()
            ]

            # Natively inject rule status if present in intake_data['_rule']
            # This avoids having to hack it in via the Makefile
            rule_info = intake_data.get("_rule", {})
            data["rule_status"] = rule_info.get("rule_status")
            data["rule_reasons"] = rule_info.get("rule_reasons", [])

            return ParsedLead.model_validate(data)
            
        except Exception as e:
            print(f"Error parsing with LLM: {str(e)}")
            raise e

    def process_lead(self, lead_dir: str) -> Optional[ParsedLead]:
        """
        Processes a lead directory containing transcript.md and intake.json.
        """
        transcript_path = os.path.join(lead_dir, "transcript.md")
        intake_path = os.path.join(lead_dir, "intake.json")

        if not os.path.exists(transcript_path) or not os.path.exists(intake_path):
            return None

        with open(transcript_path, 'r') as f:
            transcript_text = f.read()

        with open(intake_path, 'r') as f:
            intake_data = json.load(f)

        return self.parse(transcript_text, intake_data)
