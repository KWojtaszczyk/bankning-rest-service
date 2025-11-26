from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.account import AccountCreate, AccountResponse, AccountBalanceResponse
from app.services.account_service import AccountService
from app.services.account_holder_service import AccountHolderService
from app.middleware.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new bank account
    
    Requires:
    - User must have an account holder profile
    - account_type: checking, savings, or business
    - initial_deposit (optional, defaults to 0)
    """
    # Get user's account holder profile
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create an account holder profile before creating accounts"
        )
    
    try:
        account = AccountService.create_account(
            db=db,
            account_holder_id=holder.id,
            account_type=account_data.account_type,
            initial_deposit=account_data.initial_deposit,
            currency=account_data.currency
        )
        return account
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[AccountResponse])
async def list_my_accounts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all accounts for the current user"""
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder:
        return []  # No accounts if no holder profile
    
    accounts = AccountService.get_accounts_by_holder(db, holder.id)
    return accounts


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get account details by ID (must be the owner)"""
    account = AccountService.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Authorization check
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account"
        )
    
    return account


@router.get("/{account_id}/balance", response_model=AccountBalanceResponse)
async def get_account_balance(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get account balance"""
    account = AccountService.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Authorization check
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account"
        )
    
    return AccountBalanceResponse(
        account_number=account.account_number,
        balance=account.balance,
        currency=account.currency,
        status=account.status.value
    )


@router.put("/{account_id}/status")
async def update_account_status(
    account_id: int,
    new_status: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update account status (active, frozen, closed)
    
    Note: In a real system, closing accounts would require additional checks
    """
    account = AccountService.get_account_by_id(db, account_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Authorization check
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this account"
        )
    
    try:
        updated_account = AccountService.update_account_status(db, account_id, new_status)
        return {"message": f"Account status updated to {new_status}", "account": updated_account}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        