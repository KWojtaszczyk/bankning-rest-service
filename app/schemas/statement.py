from pydantic import BaseModel, Field, ConfigDict
from datetime import date, datetime
from typing import List, Optional
from decimal import Decimal


class StatementRequest(BaseModel):
    """Request to generate a statement"""
    period_start: date = Field(..., description="Statement period start date")
    period_end: date = Field(..., description="Statement period end date")
    format: str = Field(..., description="Statement format: 'pdf' or 'json'", pattern="^(pdf|json)$")


class TransactionSummary(BaseModel):
    """Transaction summary for statement"""
    date: datetime
    description: str
    debit: Optional[Decimal] = None
    credit: Optional[Decimal] = None
    balance: Decimal
    
    model_config = ConfigDict(from_attributes=True)


class StatementData(BaseModel):
    """Statement data in JSON format"""
    account_number: str
    account_holder_name: str
    statement_period_start: date
    statement_period_end: date
    opening_balance: Decimal
    closing_balance: Decimal
    total_debits: Decimal
    total_credits: Decimal
    transactions: List[TransactionSummary]
    generated_at: datetime


class StatementResponse(BaseModel):
    """Statement metadata response"""
    id: int
    account_id: int
    statement_period_start: date
    statement_period_end: date
    format: str
    file_path: Optional[str]
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
