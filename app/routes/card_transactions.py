from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from datetime import datetime, timezone

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.card import CardTransactionRequest
from app.schemas.transaction import TransactionResponse
from app.services.card_service import CardService
from app.services.account_holder_service import AccountHolderService
from app.services.account_service import AccountService
from app.middleware.auth import get_current_active_user

router = APIRouter()


def verify_card_ownership(db: Session, card_id: int, user_id: int):
    """Verify that the card belongs to the user"""
    card = CardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Check if account holder owns the account linked to the card
    holder = AccountHolderService.get_account_holder_by_user(db, user_id)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no account holder profile"
        )
        
    account = AccountService.get_account_by_id(db, card.account_id)
    if not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this card"
        )
    
    return card


@router.post("/cards/{card_id}/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def process_card_payment(
    card_id: int,
    request: CardTransactionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process a card payment transaction.
    
    Validates:
    - Card status (must be ACTIVE)
    - Daily spending limit
    - Account balance
    """
    verify_card_ownership(db, card_id, current_user.id)
    
    try:
        transaction = CardService.process_card_payment(
            db,
            card_id,
            request.amount,
            request.merchant_name,
            request.description
        )
        return transaction
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/cards/{card_id}/daily-spending")
async def get_daily_spending(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get total spending for the card today"""
    card = verify_card_ownership(db, card_id, current_user.id)
    
    today = datetime.now(timezone.utc).date()
    spent = CardService.get_daily_spending(db, card_id, today)
    remaining = card.daily_limit - spent
    
    return {
        "date": today,
        "daily_limit": card.daily_limit,
        "spent_today": spent,
        "remaining_limit": remaining
    }
