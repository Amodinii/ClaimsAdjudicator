import os
import json
import io
from typing import Dict, Any
import google.generativeai as genai
from PIL import Image
from dotenv import load_dotenv
from ..utils.logging_utils import setup_logging

load_dotenv()
logger = setup_logging()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You are an expert medical claims data extractor.
Your job is to extract structured data from medical documents (bills, prescriptions, reports) into JSON.

### EXTRACTION RULES:
1. **Date Normalization**: Convert all dates to "YYYY-MM-DD". If year is missing, assume 2024.
2. **Currency**: Extract amounts as floats (remove symbols like ₹, Rs).
3. **Line Items**: Break down the bill into individual items.
4. **Categorization (CRITICAL)**: For every item, you MUST assign a 'category' from this list:
   - "Consultation" (Doctor fees, OPD charges)
   - "Pharmacy" (Medicines, drugs)
   - "Diagnostic" (Labs, X-Ray, MRI, Blood tests)
   - "Dental" (Root canal, cleaning)
   - "Vision" (Eye test, glasses)
   - "Alternative" (Ayurveda, Homeopathy)
   - "Cosmetic" (Whitening, Botox, Hair transplant)
   - "Other" (Registration fees, etc.)
5. **Diagnosis**: Infer the diagnosis if not explicitly stated, based on the medicines/tests.

### JSON OUTPUT SCHEMA:
{
  "treatment_date": "YYYY-MM-DD",
  "total_amount": 0.0,
  "member": {
    "member_id": "string or null",
    "name": "string or null"
  },
  "hospital": {
    "name": "string or null",
    "in_network": false
  },
  "diagnosis": "string or null",
  "items": [
    {
      "name": "string",
      "amount": 0.0,
      "category": "string"
    }
  ],
  "documents": [
    {
      "type": "Prescription/Bill/Report",
      "doctor_reg": "string or null"
    }
  ],
  "_extraction_conf": 0.0 to 1.0 (Your confidence in the legibility)
}
"""

async def extract_claim_data(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    try:
        logger.info(f"Starting Gemini extraction for {filename}")
        image = Image.open(io.BytesIO(file_bytes))
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={
                "response_mime_type": "application/json" # Forces valid JSON output
            },
            system_instruction=SYSTEM_PROMPT
        )
        response = model.generate_content(
            ["Extract the claim data from this medical document.", image]
        )

        raw_json = response.text
        data = json.loads(raw_json)
        data["structured"] = False # Flag to tell the system this came from AI
        
        # If confidence wasn't returned, default to high (Flash is usually confident)
        if "_extraction_conf" not in data:
            data["_extraction_conf"] = 0.90

        logger.info("Gemini extraction successful")
        return data

    except Exception as e:
        logger.exception("Gemini Extraction failed: %s", e)
        return {}