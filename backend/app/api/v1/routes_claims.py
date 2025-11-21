from fastapi import APIRouter, HTTPException
from ...services.adjudicator import adjudicate_claim
from ...models.claim_model import ClaimModel
from ...utils.logging_utils import setup_logging
from ...utils.exception_handlers import ServiceError

router = APIRouter(prefix="/v1/claims", tags=["claims"])
logger = setup_logging()

@router.post("/submit", summary="Submit a structured claim (JSON)")
async def submit_claim(payload: ClaimModel):
    claim = payload.dict()
    try:
        if not claim.get("items") and not claim.get("total_amount"):
            raise ServiceError("Claim must include items or total_amount", code="INVALID_PAYLOAD")
        decision = adjudicate_claim(claim)
        return {"status": "ok", "decision": decision}
    except ServiceError as se:
        logger.warning("ServiceError in submit_claim: %s", se.message)
        raise HTTPException(status_code=se.status_code, detail={"code": se.code, "message": se.message})
    except Exception as e:
        logger.exception("Unexpected error in submit_claim: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
