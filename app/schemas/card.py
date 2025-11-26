from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import Optional
from decimal import Decimal

class CardBase(BaseModel):
    card_type: str = Field(..., description="Card type: debit, credit, or virtual")
    cardholder_name: str = Field(..., min_length=1, max_length=100)
    is_contactless: bool = Field(default=True)
    daily_limit: Decimal = Field(default=Decimal('1000.00'), ge=0)

class CardCreate(CardBase):
    account_id: int
    pin: str = Field(..., min_length=4, max_length=4, description="4-digit PIN")

class CardResponse(BaseModel):
    id: int
    account_id: int
    card_number_masked: str = Field(..., description="Masked card number (e.g., **** **** **** 1234)")
    card_type: str
    cardholder_name: str
    expiry_date: date
    status: str
    is_contactless: bool
    daily_limit: Decimal
    created_at: datetime
    activated_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class CardDetailsResponse(CardResponse):
    """Extended response with full card number (only for owner immediately after creation)"""
    card_number_full: str = Field(..., description="Full card number (shown only once)")
    cvv: str = Field(..., description="CVV (shown only once)")

class CardActivationRequest(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4)

class CardLimitUpdate(BaseModel):
    new_limit: Decimal = Field(..., ge=0, description="New daily spending limit")

