from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.account_holder import AccountHolderCreate, AccountHolderResponse, AccountHolderUpdate
from app.services.account_holder_service import AccountHolderService
from app.middleware.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=AccountHolderResponse, status_code=status.HTTP_201_CREATED)
async def create_account_holder(
    holder_data: AccountHolderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create account holder profile for the current user
    
    Required fields:
    - first_name, last_name, date_of_birth
    
    Optional fields:
    - phone_number, address, city, country, postal_code
    - identification_type, identification_number
    """
    try:
        holder = AccountHolderService.create_account_holder(db, current_user, holder_data)
        return holder
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=AccountHolderResponse)
async def get_my_account_holder(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get the current user's account holder profile"""
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account holder profile not found. Please create one first."
        )
    return holder


@router.get("/{holder_id}", response_model=AccountHolderResponse)
async def get_account_holder(
    holder_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get account holder by ID (must be the owner)"""
    holder = AccountHolderService.get_account_holder_by_id(db, holder_id)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account holder not found"
        )
    
    # Authorization check: user can only access their own profile
    if holder.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account holder profile"
        )
    
    return holder


@router.put("/{holder_id}", response_model=AccountHolderResponse)
async def update_account_holder(
    holder_id: int,
    holder_update: AccountHolderUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update account holder profile (must be the owner)"""
    holder = AccountHolderService.get_account_holder_by_id(db, holder_id)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account holder not found"
        )
    
    # Authorization check
    if holder.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this account holder profile"
        )
    
    updated_holder = AccountHolderService.update_account_holder(db, holder_id, holder_update)
    return updated_holder