from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional, List
from ...services.adjudicator import adjudicate_claim
from ...services.extraction_llm import extract_claim_data
from ...models.sql_models import ClaimRecord
from ...core.database import get_db
from ...utils.logging_utils import setup_logging
from ...services.narrator_llm import generate_narrative

router = APIRouter(prefix="/v1/claims", tags=["claims"])
logger = setup_logging()

@router.post("/upload", summary="Upload Multiple Documents for AI Adjudication")
async def upload_claim_document(
    files: List[UploadFile] = File(...),
    member_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        # 1. Pre-process: Collect filenames and content bytes
        filenames = [f.filename for f in files]
        logger.info(f"Received {len(files)} files for upload: {filenames}")

        file_contents = []
        for file in files:
            # Read file into memory
            content = await file.read()
            file_contents.append(content)

        # 2. AI Extraction (Pass ALL images to Gemini at once)
        extracted_data = await extract_claim_data(file_contents, filenames)
        
        if not extracted_data:
            raise HTTPException(status_code=422, detail="AI Extraction Failed. Could not read documents.")

        # 3. Member ID Override
        if member_id:
            if not extracted_data.get("member"):
                extracted_data["member"] = {}
            extracted_data["member"]["member_id"] = member_id

        # 4. Adjudication Logic (Rule Engine)
        decision_result = adjudicate_claim(extracted_data)
        
        # 5. AI Narrator (The Health Concierge)
        # Generates { "summary": "...", "medical_context": "..." }
        narrative_data = generate_narrative(extracted_data, decision_result)
        
        # Inject these fields into the result for the Frontend
        decision_result["summary_text"] = narrative_data.get("summary")
        decision_result["medical_context"] = narrative_data.get("medical_context")

        # 6. Save to Database
        combined_filenames = ", ".join(filenames)
        
        # We save the summary in the 'decision_reasons' column for historical reference
        # but keep the medical context separate (or omit if DB schema is strict, usually JSON is fine)
        db_reasons = decision_result.get("reasons", [])[:]
        if decision_result.get("summary_text"):
            db_reasons.insert(0, f"Summary: {decision_result['summary_text']}")

        db_record = ClaimRecord(
            file_name=combined_filenames,
            status=decision_result["decision"],
            total_amount=extracted_data.get("total_amount", 0.0),
            approved_amount=decision_result.get("approved_amount", 0.0),
            confidence_score=decision_result.get("confidence", 0.0),
            extracted_data=extracted_data,
            decision_reasons=db_reasons 
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        logger.info(f"Claim saved to DB with ID: {db_record.id}")

        return {
            "status": "ok",
            "claim_id": db_record.id, 
            "files_processed": filenames,
            "extracted_data": extracted_data,
            "decision": decision_result
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Upload flow failed")
        raise HTTPException(status_code=500, detail=str(e))