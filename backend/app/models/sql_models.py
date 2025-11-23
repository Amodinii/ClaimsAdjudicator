from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from datetime import datetime
from ..core.database import Base

class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    
    file_name = Column(String)
    member_id = Column(String, index=True, nullable=True)
    
    status = Column(String)
    total_amount = Column(Float)
    approved_amount = Column(Float)
    confidence_score = Column(Float)
    
    extracted_data = Column(JSON)
    decision_reasons = Column(JSON)
    image_hash = Column(String, nullable=True) # Stores the pHash fingerprint
    
    created_at = Column(DateTime, default=datetime.utcnow)