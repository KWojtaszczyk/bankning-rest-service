from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal

class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Transaction amount must be positive")
    description: Optional[str] = None

class TransferRequest(TransactionBase):
    from_account_id: int = Field(..., description="ID of the source account")
    to_account_number: str = Field(..., description="Destination account number")
    currency: str = "USD"

class TransactionFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    transaction_type: Optional[str] = None
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None

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
    
    model_config = ConfigDict(from_attributes=True)

