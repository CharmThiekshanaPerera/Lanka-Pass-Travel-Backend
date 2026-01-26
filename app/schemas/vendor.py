from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class VendorStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"

class VendorBase(BaseModel):
    business_name: str
    business_type: str
    contact_person: str
    phone_number: str
    address: str
    tax_id: Optional[str] = None
    business_registration_number: Optional[str] = None

class VendorCreate(VendorBase):
    user_id: str

class VendorUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    contact_person: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    business_registration_number: Optional[str] = None
    status: Optional[VendorStatus] = None

class VendorInDB(VendorBase):
    id: str
    user_id: str
    status: VendorStatus = VendorStatus.PENDING
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class VendorResponse(VendorBase):
    id: str
    user_id: str
    status: VendorStatus
    created_at: datetime
    user: Optional[dict] = None