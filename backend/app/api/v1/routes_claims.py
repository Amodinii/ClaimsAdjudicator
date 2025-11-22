from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import Optional
from ...services.adjudicator import adjudicate_claim
from ...services.extraction_llm import extract_claim_data
from ...models.sql_models import ClaimRecord
from ...core.database import get_db
from ...utils.logging_utils import setup_logging

router = APIRouter(prefix="/v1/claims", tags=["claims"])
logger = setup_logging()

# ... (submit_claim endpoint remains same) ...

@router.post("/upload", summary="Upload Document for AI Adjudication")
async def upload_claim_document(
    file: UploadFile = File(...),
    member_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)  # <--- Inject DB Session
):
    try:
        logger.info(f"Received file upload: {file.filename}")
        contents = await file.read()
        
        # 1. AI Extraction
        extracted_data = await extract_claim_data(contents, file.filename)
        if not extracted_data:
            raise HTTPException(status_code=422, detail="AI Extraction Failed")

        if member_id:
            if not extracted_data.get("member"):
                extracted_data["member"] = {}
            extracted_data["member"]["member_id"] = member_id

        # 2. Adjudication Logic
        decision_result = adjudicate_claim(extracted_data)
        
        # 3. SAVE TO DB (The New Part)
        db_record = ClaimRecord(
            file_name=file.filename,
            status=decision_result["decision"],
            total_amount=extracted_data.get("total_amount", 0.0),
            approved_amount=decision_result.get("approved_amount", 0.0),
            confidence_score=decision_result.get("confidence", 0.0),
            extracted_data=extracted_data,
            decision_reasons=decision_result.get("reasons", [])
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        logger.info(f"Claim saved to DB with ID: {db_record.id}")

        return {
            "status": "ok",
            "claim_id": db_record.id, # Return DB ID for future reference
            "file_processed": file.filename,
            "extracted_data": extracted_data,
            "decision": decision_result
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Upload flow failed")
        raise HTTPException(status_code=500, detail=str(e))