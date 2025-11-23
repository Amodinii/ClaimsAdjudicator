from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date

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
        # 1. Pre-process
        filenames = [f.filename for f in files]
        logger.info(f"Received {len(files)} files: {filenames}")

        file_contents = []
        for file in files:
            content = await file.read()
            file_contents.append(content)

        # 2. AI Extraction
        extracted_data = await extract_claim_data(file_contents, filenames)
        if not extracted_data:
            raise HTTPException(status_code=422, detail="AI Extraction Failed.")

        # 3. IDENTIFY MEMBER (THE FIX)
        # Logic: Form Input > Extracted ID > Extracted Name > "Unknown"
        final_member_id = None
        
        # Check AI extraction first
        ai_member = extracted_data.get("member") or {}
        ai_id = ai_member.get("member_id")
        ai_name = ai_member.get("name")

        if member_id: 
            final_member_id = member_id # Priority 1: Form input
        elif ai_id:
            final_member_id = ai_id     # Priority 2: AI Extracted ID
        elif ai_name:
            final_member_id = ai_name   # Priority 3: AI Extracted Name (Fallback)
        else:
            final_member_id = "Unknown_Guest"

        # Update the data object so Adjudicator has it
        if not extracted_data.get("member"): extracted_data["member"] = {}
        extracted_data["member"]["member_id"] = final_member_id

        # 4. HISTORICAL VELOCITY CHECK
        todays_claim_count = 0
        if final_member_id != "Unknown_Guest":
            today = date.today()
            # Count how many times this ID (or Name) appears in DB today
            todays_claim_count = db.query(ClaimRecord).filter(
                ClaimRecord.member_id == final_member_id,
                func.date(ClaimRecord.created_at) == today
            ).count()
            
            logger.info(f"VELOCITY CHECK: Member '{final_member_id}' has {todays_claim_count} previous claims today.")
        
        extracted_data["prev_claims_same_day"] = todays_claim_count

        # 5. Adjudication
        decision_result = adjudicate_claim(extracted_data)
        
        # 6. Narrator
        narrative_data = generate_narrative(extracted_data, decision_result)
        decision_result["summary_text"] = narrative_data.get("summary")
        decision_result["medical_context"] = narrative_data.get("medical_context")

        # 7. Save to DB
        combined_filenames = ", ".join(filenames)
        
        db_reasons = decision_result.get("reasons", [])[:]
        if decision_result.get("summary_text"):
            db_reasons.insert(0, f"Summary: {decision_result['summary_text']}")

        db_record = ClaimRecord(
            file_name=combined_filenames,
            member_id=final_member_id, # Saving the Name/ID used for lookup
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