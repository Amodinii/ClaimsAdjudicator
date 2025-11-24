import imagehash
from PIL import Image
import io
from sqlalchemy.orm import Session
from ..models.sql_models import ClaimRecord
from ..utils.logging_utils import setup_logging

logger = setup_logging()

def calculate_phash(image_bytes: bytes) -> str:
    """
    Generates a Difference Hash (dHash) of an image.
    dHash is better for documents/text than pHash because it tracks 
    gradients (text lines) rather than just frequency structure.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        hash_obj = imagehash.dhash(img, hash_size=8)
        
        return str(hash_obj)
    except Exception as e:
        logger.error(f"Failed to generate Hash: {e}")
        return None


def check_duplicate_images(current_phash: str, db: Session, threshold: int = 3) -> bool:
    """
    Checks DB for images that look visually identical.
    
    Threshold Logic for dHash (64-bit):
    0: Exact duplicate
    1-2: Likely same image (resized/compressed)
    3-5: Same template/layout but potentially different content
    >10: Different images
    """
    if not current_phash:
        return False

    # Check against the last 100 claims to keep it fast
    previous_claims = db.query(ClaimRecord).filter(ClaimRecord.image_hash.isnot(None)).order_by(ClaimRecord.id.desc()).limit(100).all()
    
    try:
        current_hash_obj = imagehash.hex_to_hash(current_phash)
    except Exception:
        return False
    
    for claim in previous_claims:
        try:
            prev_hash_obj = imagehash.hex_to_hash(claim.image_hash)
            diff = current_hash_obj - prev_hash_obj
            
            if diff <= threshold:
                logger.warning(f"Duplicate Image Detected! Match with Claim ID {claim.id} (Diff: {diff})")
                return True 
        except Exception:
            continue
            
    return False