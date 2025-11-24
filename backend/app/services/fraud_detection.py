import hashlib
from sqlalchemy.orm import Session
from ..models.sql_models import ClaimRecord
from ..utils.logging_utils import setup_logging

logger = setup_logging()

def calculate_phash(image_bytes: bytes) -> str:
    """
    Generates a SHA-256 cryptographic hash of the file.
    This ensures that EXACTLY identical files are flagged,
    but similar-looking bills (same template, different text) are allowed.
    """
    try:
        # Calculate SHA-256 hash of the raw bytes
        file_hash = hashlib.sha256(image_bytes).hexdigest()
        return file_hash
    except Exception as e:
        logger.error(f"Failed to generate hash: {e}")
        return None

def check_duplicate_images(current_hash: str, db: Session) -> bool:
    """
    Checks DB for the exact same file hash.
    """
    if not current_hash:
        return False

    exists = db.query(ClaimRecord).filter(
        ClaimRecord.image_hash == current_hash
    ).first()
    
    if exists:
        logger.warning(f"Duplicate File Detected! Exact match with Claim ID {exists.id}")
        return True
        
    return False