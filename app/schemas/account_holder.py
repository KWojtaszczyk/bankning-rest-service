from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional

class AccountHolderBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    date_of_birth: date
    phone_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    identification_type: Optional[str] = Field(None, description="passport, drivers_license, national_id")
    identification_number: Optional[str] = Field(None, max_length=50)

class AccountHolderCreate(AccountHolderBase):
    pass

class AccountHolderUpdate(BaseModel):
    phone_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

class AccountHolderResponse(AccountHolderBase):
    id: int
    user_id: int
    kyc_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
