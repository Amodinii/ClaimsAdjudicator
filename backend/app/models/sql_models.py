from sqlalchemy import Column, Integer, String, Float, JSON, DateTime
from datetime import datetime
from ..core.database import Base

class ClaimRecord(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    
    file_name = Column(String)
    status = Column(String)  # APPROVED, REJECTED, MANUAL_REVIEW
    total_amount = Column(Float)
    approved_amount = Column(Float)
    confidence_score = Column(Float)
    
    extracted_data = Column(JSON)
    decision_reasons = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)