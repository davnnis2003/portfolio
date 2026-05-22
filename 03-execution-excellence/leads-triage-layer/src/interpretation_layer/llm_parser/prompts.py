SYSTEM_PROMPT = """
You are a technical data extractor for ClimateTech. 
You extract structured building information from transcripts.
You MUST respond with a valid JSON object only.
"""

PARSER_PROMPT = """
Task: Extract entities, contradictions, and risk factors from the data below.

### Call Transcript:
{transcript}

### Intake Data:
{intake}

### JSON Output Format:
{{
  "entities": {{
    "house_type": "Extract house type (e.g. EFH, Bungalow, MFH)",
    "insulation_type": "Extract requested insulation",
    "cavity": "Extract cavity size or presence",
    "access": "Extract access constraints",
    "region": "Extract region",
    "constraints": "Extract technical constraints"
  }},
  "contradictions": [
    {{
      "field": "Field name",
      "transcript_value": "Value from transcript",
      "intake_value": "Value from intake",
      "reason": "Reason for discrepancy"
    }}
  ],
  "risk_factors": [
    {{
      "tag": "Risk tag",
      "description": "Risk description",
      "severity": "LOW, MEDIUM, or HIGH"
    }}
  ]
}}

### CRITICAL INSTRUCTIONS:
1. ONLY include entries in "contradictions" if the transcript value SIGNIFICANTLY differs from the intake value.
2. If the values match or are effectively the same, DO NOT include them in the list.
3. If there are no contradictions, return an empty list: [].
"""
