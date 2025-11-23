import imagehash
from PIL import Image
import io
from sqlalchemy.orm import Session
from ..models.sql_models import ClaimRecord
from ..utils.logging_utils import setup_logging

logger = setup_logging()

def calculate_phash(image_bytes: bytes) -> str:
    """
    Generates a Perceptual Hash (fingerprint) of an image.
    Resistant to resizing, rotation, and minor color changes.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # phash computes a hash based on visual frequencies
        hash_obj = imagehash.phash(img)
        return str(hash_obj)
    except Exception as e:
        logger.error(f"Failed to generate pHash: {e}")
        return None

def check_duplicate_images(current_phash: str, db: Session, threshold: int = 5) -> bool:
    """
    Checks DB for images that look visually similar.
    Hamming distance < 5 usually means it's the same image processed slightly differently.
    """
    if not current_phash:
        return False

    # Check against the last 100 claims to keep it fast
    previous_claims = db.query(ClaimRecord).filter(ClaimRecord.image_hash.isnot(None)).order_by(ClaimRecord.id.desc()).limit(100).all()
    
    current_hash_obj = imagehash.hex_to_hash(current_phash)
    
    for claim in previous_claims:
        try:
            prev_hash_obj = imagehash.hex_to_hash(claim.image_hash)
            diff = current_hash_obj - prev_hash_obj
            
            if diff < threshold:
                logger.warning(f"Duplicate Image Detected! Match with Claim ID {claim.id} (Diff: {diff})")
                return True 
        except Exception:
            continue
            
    return False