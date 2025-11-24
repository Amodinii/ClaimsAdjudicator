import os
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Body
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date
from pydantic import BaseModel 

from ...services.adjudicator import adjudicate_claim
from ...services.extraction_llm import extract_claim_data
from ...models.sql_models import ClaimRecord
from ...core.database import get_db
from ...utils.logging_utils import setup_logging
from ...services.narrator_llm import generate_narrative
from ...services.fraud_detection import calculate_phash, check_duplicate_images

cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET"),
  secure = True
)

router = APIRouter(prefix="/v1/claims", tags=["claims"])
logger = setup_logging()

class ClaimUpdate(BaseModel):
    status: str
    approved_amount: float
    decision_reasons: List[str]

@router.get("/pending", summary="Get claims requiring manual review")
async def get_pending_claims(db: Session = Depends(get_db)):
    claims = db.query(ClaimRecord).filter(
        ClaimRecord.status == "MANUAL_REVIEW"
    ).order_by(ClaimRecord.created_at.desc()).all()
    return claims

@router.put("/{claim_id}", summary="Admin Override Claim Decision")
async def update_claim_status(
    claim_id: int,
    update_data: ClaimUpdate,
    db: Session = Depends(get_db)
):
    claim = db.query(ClaimRecord).filter(ClaimRecord.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    
    logger.info(f"Admin overriding claim {claim_id} to {update_data.status}")
    
    claim.status = update_data.status
    claim.approved_amount = update_data.approved_amount
    claim.decision_reasons = update_data.decision_reasons
    
    db.commit()
    db.refresh(claim)
    return {"status": "ok", "claim_id": claim.id, "new_status": claim.status}

@router.post("/upload", summary="Upload Multiple Documents for AI Adjudication")
async def upload_claim_document(
    files: List[UploadFile] = File(...),
    member_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    try:
        original_filenames = [f.filename for f in files]
        logger.info(f"Received {len(files)} files for upload: {original_filenames}")

        file_contents = []
        computed_hashes = []
        uploaded_urls = [] 
        is_duplicate_image = False

        for file in files:
            # 1. Read file into memory
            content = await file.read()
            file_contents.append(content)
            
            # 2. Upload to Cloudinary
            try:
                # We upload the bytes ('content') directly
                # resource_type="auto" handles PDFs and Images automatically
                upload_result = cloudinary.uploader.upload(content, resource_type="auto")
                secure_url = upload_result.get("secure_url")
                uploaded_urls.append(secure_url)
                logger.info(f"Uploaded to Cloudinary: {secure_url}")
            except Exception as cloud_err:
                logger.error(f"Cloudinary upload failed for {file.filename}: {cloud_err}")
                raise HTTPException(status_code=500, detail="Failed to upload image to cloud storage")

            # 3. Calculate Hash for Fraud Detection
            phash = calculate_phash(content)
            if phash:
                computed_hashes.append(phash)
                if check_duplicate_images(phash, db):
                    is_duplicate_image = True

        # Combine URLs for storage (comma separated)
        combined_file_urls = ", ".join(uploaded_urls)

        # --- DUPLICATE HANDLING ---
        if is_duplicate_image:
            logger.warning("Duplicate detected. Flagging for review.")
            extracted_data = {"total_amount": 0.0, "diagnosis": "Potential Duplicate Upload"}
            decision_result = {
                "decision": "MANUAL_REVIEW",
                "approved_amount": 0.0,
                "reasons": ["DUPLICATE_IMAGE_DETECTED"],
                "confidence": 0.0,
                "summary_text": "This document appears identical to a previously submitted claim. Flagged for manual verification.",
                "medical_context": "Analysis paused due to duplicate detection."
            }
            
            db_record = ClaimRecord(
                file_name=combined_file_urls, 
                status="MANUAL_REVIEW",
                total_amount=0.0,
                approved_amount=0.0,
                confidence_score=0.0,
                extracted_data=extracted_data,
                decision_reasons=["DUPLICATE_IMAGE_DETECTED"],
                image_hash=computed_hashes[0] if computed_hashes else None
            )
            db.add(db_record)
            db.commit()
            db.refresh(db_record)
            
            return {
                "status": "ok",
                "claim_id": db_record.id,
                "files_processed": uploaded_urls,
                "extracted_data": extracted_data,
                "decision": decision_result
            }

        # --- AI EXTRACTION ---
        extracted_data = await extract_claim_data(file_contents, original_filenames)
        if not extracted_data:
            raise HTTPException(status_code=422, detail="AI Extraction Failed.")

        # --- MEMBER RESOLUTION ---
        final_member_id = None
        if member_id: final_member_id = member_id
        elif extracted_data.get("member", {}).get("member_id"): final_member_id = extracted_data.get("member", {}).get("member_id")
        elif extracted_data.get("member", {}).get("name"): final_member_id = extracted_data.get("member", {}).get("name")
        else: final_member_id = "Unknown_Guest"

        if not extracted_data.get("member"): extracted_data["member"] = {}
        extracted_data["member"]["member_id"] = final_member_id

        # --- VELOCITY CHECK ---
        todays_claim_count = 0
        if final_member_id != "Unknown_Guest":
            today = date.today()
            todays_claim_count = db.query(ClaimRecord).filter(
                ClaimRecord.member_id == final_member_id,
                func.date(ClaimRecord.created_at) == today
            ).count()
            logger.info(f"VELOCITY CHECK: Member '{final_member_id}' has {todays_claim_count} previous claims today.")
        
        extracted_data["prev_claims_same_day"] = todays_claim_count

        # --- ADJUDICATION ---
        decision_result = adjudicate_claim(extracted_data)
        
        # --- NARRATOR ---
        narrative_data = generate_narrative(extracted_data, decision_result)
        decision_result["summary_text"] = narrative_data.get("summary")
        decision_result["medical_context"] = narrative_data.get("medical_context")

        # --- SAVE TO DATABASE ---
        db_reasons = decision_result.get("reasons", [])[:]
        if decision_result.get("summary_text"):
            db_reasons.insert(0, f"Summary: {decision_result['summary_text']}")

        db_record = ClaimRecord(
            file_name=combined_file_urls, # STORE URL NOT FILENAME
            member_id=final_member_id,
            status=decision_result["decision"],
            total_amount=extracted_data.get("total_amount", 0.0),
            approved_amount=decision_result.get("approved_amount", 0.0),
            confidence_score=decision_result.get("confidence", 0.0),
            extracted_data=extracted_data,
            decision_reasons=db_reasons,
            image_hash=computed_hashes[0] if computed_hashes else None
        )
        db.add(db_record)
        db.commit()
        db.refresh(db_record)
        
        logger.info(f"Claim saved to DB with ID: {db_record.id}")

        return {
            "status": "ok",
            "claim_id": db_record.id, 
            "files_processed": uploaded_urls, # Return URLs
            "extracted_data": extracted_data,
            "decision": decision_result
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.exception("Upload flow failed")
        raise HTTPException(status_code=500, detail=str(e))