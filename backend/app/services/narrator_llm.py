import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from ..utils.logging_utils import setup_logging

load_dotenv()
logger = setup_logging()

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Reuse the same stable model
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You are a helpful Insurance Claims & Health Assistant.
Analyze the claim data and return a JSON object with two fields:
1. "summary": A 2-3 sentence explanation of the APPROVAL/REJECTION decision (financial focus). 
   - CRITICAL: All monetary values MUST be in Indian Rupees (₹). Do NOT use '$'.
   - Mention specific reasons like limits or exclusions if applicable.
2. "medical_context": A short, empathetic explanation of the diagnosis/tests and 2 simple recovery tips.
   - If extraction shows lab results, briefly explain what they mean in plain English.
   - ALWAYS end with: "Please consult your doctor for medical advice."
"""

def generate_narrative(claim_data: dict, decision_result: dict) -> dict:
    try:
        # Construct Context
        diagnosis = claim_data.get("diagnosis", "Unknown Condition")
        total = claim_data.get("total_amount", 0)
        approved = decision_result.get("approved_amount", 0)
        status = decision_result.get("decision", "PENDING")
        reasons = ", ".join(decision_result.get("reasons", []))
        
        # Format Lab Results for Prompt
        lab_text = "No lab report found."
        if claim_data.get("lab_results"):
            lab_text = "Lab Report Data:\n"
            for res in claim_data.get("lab_results"):
                lab_text += f"- {res.get('test_name')}: {res.get('result')} (Range: {res.get('normal_range')})\n"
        
        # Build the User Prompt
        prompt = f"""
        Analyze this claim and provide the narrative JSON.
        
        Context:
        - Diagnosis: {diagnosis}
        - Status: {status} (Amount: {total})
        - Technical Reasons: {reasons}
        - {lab_text}
        """

        # Initialize Model with JSON Enforcement
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={"response_mime_type": "application/json"},
            system_instruction=SYSTEM_PROMPT
        )

        # Generate
        response = model.generate_content(prompt)
        
        # Parse
        content = json.loads(response.text)
        return content

    except Exception as e:
        logger.error(f"Narrator LLM failed: {e}")
        # Fallback if AI fails
        return {
            "summary": f"The claim was processed with status: {decision_result.get('decision')}. Please review the breakdown for details.",
            "medical_context": "Health information unavailable at this time."
        }