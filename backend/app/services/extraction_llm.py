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

# Using the latest stable Flash model
MODEL_NAME = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You are an expert medical claims data extractor and medical coder.
Your job is to extract structured data from medical documents (bills, prescriptions, reports) into JSON.

### EXTRACTION RULES:
1. **Combine Information**: Treat multiple images as ONE single claim context.
2. **Date Normalization**: Convert all dates to "YYYY-MM-DD". If year is missing, assume current year.
3. **Currency**: Extract amounts as floats (remove symbols like ₹, Rs).
4. **Line Item Categorization**: Map items to standard categories (Consultation, Pharmacy, Diagnostic, Dental - Routine, Dental - Cosmetic, Vision, Alternative, Procedure, Wellness, Other).
5. **Lab Report Extraction (CRITICAL)**: 
   If the document contains a Diagnostic/Lab Report (like Blood Test, MRI):
   - Extract the specific test results into a "lab_results" array.
   - Capture: Test Name, Measured Result, and Normal Range.
   - Do NOT add these diagnostic values to the "items" (financial) list unless there is a price attached.
6. **Handwriting Handling**: 
   - If the document is handwritten (like a prescription), use context to infer unclear words. 
   - For example, if you see "P_r_c_t_m_l", infer "Paracetamol". 
   - If a word is illegible, return "[Illegible]".
   

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
  "lab_results": [
    {
      "test_name": "string (e.g. Hemoglobin)",
      "result": "string (e.g. 14.2 g/dL)",
      "normal_range": "string (e.g. 13.0 - 17.0)"
    }
  ],
  "documents": [
    {
      "type": "Prescription/Bill/Report",
      "doctor_reg": "string or null"
    }
  ],
  "_extraction_conf": 0.95
}
"""

async def extract_claim_data(file_contents: list[bytes], filenames: list[str]) -> Dict[str, Any]:
    try:
        logger.info(f"Starting Gemini extraction for {len(filenames)} files: {filenames}")
        
        images = []
        for content in file_contents:
            images.append(Image.open(io.BytesIO(content)))

        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            generation_config={"response_mime_type": "application/json"},
            system_instruction=SYSTEM_PROMPT
        )

        prompt_content = ["Extract ONE combined claim JSON from these documents. Merge all data.", *images]
        
        response = model.generate_content(prompt_content)
        raw_json = response.text
        data = json.loads(raw_json)

        # --- HANDLE LIST RESPONSE (Merge logic) ---
        if isinstance(data, list):
            logger.warning("Gemini returned a list. Merging dictionaries...")
            merged_data = {}
            items_acc = []
            docs_acc = []
            lab_acc = []
            
            for entry in data:
                if not isinstance(entry, dict): continue
                
                for k, v in entry.items():
                    if k not in ["items", "documents", "lab_results"] and v is not None:
                        merged_data[k] = v
                
                if "items" in entry and isinstance(entry["items"], list):
                    items_acc.extend(entry["items"])
                if "documents" in entry and isinstance(entry["documents"], list):
                    docs_acc.extend(entry["documents"])
                if "lab_results" in entry and isinstance(entry["lab_results"], list):
                    lab_acc.extend(entry["lab_results"])
            
            merged_data["items"] = items_acc
            merged_data["documents"] = docs_acc
            merged_data["lab_results"] = lab_acc
            data = merged_data

        # Post-processing
        data["structured"] = False
        if "_extraction_conf" not in data:
            data["_extraction_conf"] = 0.90
            
        # Recalculate total if missing
        if not data.get("total_amount") and data.get("items"):
            data["total_amount"] = sum(float(i.get("amount") or 0) for i in data["items"] if i)

        return data

    except Exception as e:
        logger.exception("Gemini Extraction failed: %s", e)
        return {}