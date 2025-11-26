from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from app.database import get_db
from app.models.user import User
from app.schemas.transaction import (
    TransactionResponse, 
    TransferRequest, 
    TransactionFilter
)
from app.services.transaction_service import TransactionService
from app.services.account_service import AccountService
from app.services.account_holder_service import AccountHolderService
from app.middleware.auth import get_current_active_user

router = APIRouter()

@router.post("/transfer", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def transfer_funds(
    transfer_data: TransferRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Initiate a money transfer between accounts.
    """
    # 1. Verify source account ownership
    account = AccountService.get_account_by_id(db, transfer_data.from_account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Source account not found")
        
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder or account.account_holder_id != holder.id:
        raise HTTPException(status_code=403, detail="Not authorized to use this account")

    try:
        transaction = TransactionService.transfer_funds(
            db=db,
            from_account_id=transfer_data.from_account_id,
            to_account_number=transfer_data.to_account_number,
            amount=transfer_data.amount,
            description=transfer_data.description
        )
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/accounts/{account_id}/transactions", response_model=List[TransactionResponse])
async def get_account_transactions(
    account_id: int,
    skip: int = 0,
    limit: int = 20,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    transaction_type: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for a specific account with filtering.
    """
    # Verify account ownership
    account = AccountService.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
        
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder or account.account_holder_id != holder.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this account's transactions")
    
    filters = TransactionFilter(
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        min_amount=min_amount,
        max_amount=max_amount
    )
    
    return TransactionService.get_transaction_history(
        db=db,
        account_id=account_id,
        skip=skip,
        limit=limit,
        filters=filters
    )

@router.post("/transactions/{transaction_id}/rollback", response_model=TransactionResponse)
async def rollback_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Rollback (reverse) a transaction.
    Only the sender of the original transaction can initiate a rollback.
    """
    # We need to fetch the transaction to check ownership
    # But TransactionService.rollback_transaction expects us to verify ownership?
    # Actually, let's fetch it here to verify ownership first.
    # Or better, let the service handle it but we need to pass user_id?
    # The service method signature is `rollback_transaction(db, transaction_id, user_id)`
    # But inside the service, I commented that we should verify ownership.
    
    # Let's verify ownership here for safety
    # We need to find the transaction first
    from app.models.transaction import Transaction
    txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    # Check if current user owns the source account
    account = AccountService.get_account_by_id(db, txn.from_account_id)
    if not account:
         raise HTTPException(status_code=404, detail="Source account not found")
         
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder or account.account_holder_id != holder.id:
        raise HTTPException(status_code=403, detail="Not authorized to rollback this transaction")

    try:
        reversal = TransactionService.rollback_transaction(db, transaction_id, current_user.id)
        return reversal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
