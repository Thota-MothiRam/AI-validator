


import json
from openai import OpenAI
from config import Config
from logger_config import setup_logging

trace = setup_logging("validator_svc")


def analyze_lead(full_context_json):
    """
    Performs AI fraud detection using the stored procedure JSON.
    Returns structured dict + readable narrative.
    """

    api_key = Config.OPENAI_API_KEY
    if not api_key:
        trace.error("OpenAI API Key missing!")
        return {
            "overall_decision": "Deny",
            "confidence_score": 0,
            "AISummary": "System Config Error",
            "field_analysis": {},
            "Readable_Report": "System configuration error."
        }

    client = OpenAI(api_key=api_key)

    prompt = f"""
You are a senior fraud detection analyst for a fire truck sales company.

CRITICAL RULES:
- Missing data is NOT fraud.
- Only flag FRAUD if there are strong contradictions or obviously fake data.
- Minor spelling differences are normal.
- Volunteer departments may use Gmail/Hotmail.
- Abbreviations in department names are normal.
- Do NOT assume fraud without evidence.

TASK:
Analyze the lead using ALL JSON data provided from the database. Return:
- overall_decision ("Approve" or "Deny")
- confidence_score (0-100)
- AISummary (2-4 sentences)
- field_analysis (status and reason for each key field)

FULL DATABASE DATA:
{json.dumps(full_context_json, indent=2)}

STRICT JSON OUTPUT FORMAT:
{{
  "overall_decision": "Approve or Deny",
  "confidence_score": 0,
  "AISummary": "",
  "field_analysis": {{
    "first_name": {{"status": "", "reason": ""}},
    "last_name": {{"status": "", "reason": ""}},
    "job_title": {{"status": "", "reason": ""}},
    "company_name": {{"status": "", "reason": ""}},
    "llm_company_name": {{"status": "", "reason": ""}},
    "email": {{"status": "", "reason": ""}},
    "phone": {{"status": "", "reason": ""}},
    "zip": {{"status": "", "reason": ""}},
    "state": {{"status": "", "reason": ""}},
    "address": {{"status": "", "reason": ""}},
    "historical_data": {{"status": "", "reason": ""}},
    "account_details": {{"status": "", "reason": ""}}
  }}
}}
"""

    try:
        # ----------- FIRST CALL (STRUCTURED ANALYSIS) -----------
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict JSON returning fraud analysis engine."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty AI response")

        result = json.loads(content)

        # ----------- SECOND CALL (READABLE SUMMARY) -----------
        readable_report = generate_readable_summary(result, client)

        # Attach narrative without breaking existing structure
        result["Readable_Report"] = readable_report
        trace.info(f"AI Result: {result}")
        trace.info(f"AI Decision: {result.get('overall_decision')} | Confidence: {result.get('confidence_score')}")
        return result

    except Exception as e:
        trace.error(f"AI Error: {str(e)}")
        return {
            "overall_decision": "Deny",
            "confidence_score": 0,
            "AISummary": "AI Processing Error",
            "field_analysis": {},
            "Readable_Report": "Readable summary generation failed."
        }


# =========================================================
# READABLE BUSINESS NARRATIVE GENERATOR
# =========================================================
def generate_readable_summary(result_json, client):
    """
    Converts structured fraud JSON into a professional business narrative.
    """

    narrative_prompt = f"""
You are a professional fraud investigation report writer.

Using the structured fraud findings below,
write a detailed business explanation of WHY this decision was made.

IMPORTANT:
- Do NOT repeat the summary.
- Expand on field inconsistencies and cross-field signals.
- Explain patterns and validation findings.
- Professional tone.
- 4–6 sentences.

STRUCTURED FINDINGS:
{json.dumps(result_json, indent=2)}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You write executive fraud investigation summaries."},
                {"role": "user", "content": narrative_prompt}
            ],
            temperature=0.3
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        trace.error(f"Narrative Generation Error: {str(e)}")
        return "Readable summary generation failed."
    



