from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class Document(BaseModel):
    type: Optional[str] = None
    doctor_reg: Optional[str] = None
    raw_text: Optional[str] = None

class Hospital(BaseModel):
    name: Optional[str] = None
    in_network: Optional[bool] = False

class Member(BaseModel):
    member_id: Optional[str] = None
    join_date: Optional[str] = None

class Item(BaseModel):
    name: str
    amount: float
    category: Optional[str] = None

class ClaimModel(BaseModel):
    treatment_date: Optional[str] = None
    items: Optional[List[Item]] = Field(default_factory=list)
    total_amount: Optional[float] = 0.0
    documents: Optional[List[Document]] = Field(default_factory=list)
    member: Optional[Member] = None
    hospital: Optional[Hospital] = None
    diagnosis: Optional[str] = None
    prev_claims_same_day: Optional[int] = 0
    _extraction_conf: Optional[float] = 0.9
    structured: Optional[bool] = False
    class Config:
        extra = "allow"
