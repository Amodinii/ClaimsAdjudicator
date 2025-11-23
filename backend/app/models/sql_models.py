from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from datetime import datetime
from ..core.database import Base

class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    
    file_name = Column(String)
    # --- NEW COLUMN ---
    member_id = Column(String, index=True, nullable=True) 
    
    status = Column(String)
    total_amount = Column(Float)
    approved_amount = Column(Float)
    confidence_score = Column(Float)
    
    extracted_data = Column(JSON)
    decision_reasons = Column(JSON)
    image_hash = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)