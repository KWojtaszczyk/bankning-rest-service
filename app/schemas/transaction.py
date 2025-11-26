from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from decimal import Decimal

class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Transaction amount must be positive")
    description: Optional[str] = None

class TransferRequest(TransactionBase):
    from_account_number: str
    to_account_number: str
    currency: str = "USD"

class TransactionResponse(BaseModel):
    id: int
    transaction_type: str
    from_account_id: Optional[int]
    to_account_id: Optional[int]
    amount: Decimal
    currency: str
    status: str
    description: Optional[str]
    reference_number: str
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

