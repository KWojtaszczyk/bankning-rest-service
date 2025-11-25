from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal


class AccountBase(BaseModel):
    account_type: str = Field(..., description="Account type: checking, savings, or business")
    currency: str = Field(default="USD", description="Currency code")


class AccountCreate(AccountBase):
    initial_deposit: Optional[Decimal] = Field(default=0.00, ge=0)


class AccountResponse(AccountBase):
    id: int
    account_holder_id: int
    account_number: str
    balance: Decimal
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AccountBalanceResponse(BaseModel):
    account_number: str
    balance: Decimal
    currency: str
    status: str
