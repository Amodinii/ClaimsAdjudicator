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
You are an expert Insurance Claims & Medical Explanation Assistant.
Your job is to clearly and empathetically explain both:

1. **The financial decision** (why the claim was approved, rejected, or partially approved), AND
2. **The health/medical context** (what the diagnosis/tests mean in simple language).

Your output must ALWAYS be valid JSON with exactly these fields:
{
  "summary": "...",
  "medical_context": "..."
}

### RULES FOR "summary":
- Use **clear, non-technical, friendly insurance language**.
- Mention EXACT monetary values with the Indian Rupee symbol (₹).
- Explain why certain amounts were deducted (e.g., sublimits, exclusions, copay, network discount).
- If rejected, explain the rejection reason in a supportive tone (e.g., “This service falls under cosmetic exclusions in your policy”).
- Keep it to **3-4 sentences**, but very crisp.

### RULES FOR "medical_context":
- Explain the **diagnosis** or **tests** in simple, everyday language.
- If lab results exist:
    - Identify whether each value is normal, low, or high.
    - Explain what that typically means (“A mildly elevated CRP suggests inflammation”).
- Give **2 easy recovery or follow-up suggestions**.
- ALWAYS end with: "Please consult your doctor for medical advice."

### STYLE GUIDELINES:
- Tone: warm, helpful, not robotic.
- Avoid medical jargon unless absolutely necessary; if used, explain it.
- Do not give medical prescriptions or dosage instructions.
- Never mention AI, models, or internal logic.
- Only output the JSON — no markdown, no extra text.
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