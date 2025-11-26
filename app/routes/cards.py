from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from app.database import get_db
from app.schemas.card import CardCreate, CardResponse, CardDetailsResponse, CardActivationRequest, CardLimitUpdate
from app.services.card_service import CardService
from app.services.account_holder_service import AccountHolderService
from app.services.account_service import AccountService
from app.middleware.auth import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=CardDetailsResponse, status_code=status.HTTP_201_CREATED)
async def create_card(
    card_data: CardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new card (debit, credit, or virtual)
    
    ⚠️ IMPORTANT: Card number and CVV are shown ONLY ONCE during creation.
    Save them securely - they cannot be retrieved later!
    
    Requires:
    - account_id: Account to link card to
    - card_type: debit, credit, or virtual
    - cardholder_name: Name to print on card
    - pin: 4-digit PIN for card activation
    """
    # Get user's account holder profile
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create an account holder profile first"
        )
    
    # Verify account belongs to user
    account = AccountService.get_account_by_id(db, card_data.account_id)
    if not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not found or does not belong to you"
        )
    
    try:
        card, full_card_number, cvv = CardService.create_card(db, card_data, holder.id)
        
        # Return full details (only shown once!)
        return CardDetailsResponse(
            id=card.id,
            account_id=card.account_id,
            card_number_masked=CardService.mask_card_number(full_card_number),
            card_number_full=full_card_number,
            card_type=card.card_type.value,
            cardholder_name=card.cardholder_name,
            expiry_date=card.expiry_date,
            cvv=cvv,
            status=card.status.value,
            is_contactless=card.is_contactless,
            daily_limit=card.daily_limit,
            created_at=card.created_at,
            activated_at=card.activated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/", response_model=List[CardResponse])
async def list_my_cards(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all cards for the current user (across all accounts)"""
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder:
        return []
    
    cards = CardService.get_cards_by_holder(db, holder.id)
    
    # Return with masked card numbers
    return [
        CardResponse(
            id=card.id,
            account_id=card.account_id,
            card_number_masked=CardService.mask_card_number(card.card_number),
            card_type=card.card_type.value,
            cardholder_name=card.cardholder_name,
            expiry_date=card.expiry_date,
            status=card.status.value,
            is_contactless=card.is_contactless,
            daily_limit=card.daily_limit,
            created_at=card.created_at,
            activated_at=card.activated_at
        )
        for card in cards
    ]


@router.get("/{card_id}", response_model=CardResponse)
async def get_card_details(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get card details by ID (card number is masked)
    
    Note: Full card number and CVV are NEVER shown after initial creation
    """
    card = CardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Authorization check
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    account = AccountService.get_account_by_id(db, card.account_id)
    
    if not holder or not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this card"
        )
    
    return CardResponse(
        id=card.id,
        account_id=card.account_id,
        card_number_masked=CardService.mask_card_number(card.card_number),
        card_type=card.card_type.value,
        cardholder_name=card.cardholder_name,
        expiry_date=card.expiry_date,
        status=card.status.value,
        is_contactless=card.is_contactless,
        daily_limit=card.daily_limit,
        created_at=card.created_at,
        activated_at=card.activated_at
    )


@router.post("/{card_id}/activate", response_model=CardResponse)
async def activate_card(
    card_id: int,
    activation_data: CardActivationRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Activate a card using the PIN set during creation
    
    Cards must be activated before use
    """
    card = CardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Authorization check
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    account = AccountService.get_account_by_id(db, card.account_id)
    
    if not holder or not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to activate this card"
        )
    
    try:
        activated_card = CardService.activate_card(db, card_id, activation_data.pin)
        if not activated_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Card not found"
            )
        
        return CardResponse(
            id=activated_card.id,
            account_id=activated_card.account_id,
            card_number_masked=CardService.mask_card_number(activated_card.card_number),
            card_type=activated_card.card_type.value,
            cardholder_name=activated_card.cardholder_name,
            expiry_date=activated_card.expiry_date,
            status=activated_card.status.value,
            is_contactless=activated_card.is_contactless,
            daily_limit=activated_card.daily_limit,
            created_at=activated_card.created_at,
            activated_at=activated_card.activated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{card_id}/deactivate", response_model=CardResponse)
async def deactivate_card(
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate/block a card
    
    Use this if card is lost, stolen, or compromised
    """
    card = CardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Authorization check
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    account = AccountService.get_account_by_id(db, card.account_id)
    
    if not holder or not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to deactivate this card"
        )
    
    try:
        deactivated_card = CardService.deactivate_card(db, card_id)
        
        return CardResponse(
            id=deactivated_card.id,
            account_id=deactivated_card.account_id,
            card_number_masked=CardService.mask_card_number(deactivated_card.card_number),
            card_type=deactivated_card.card_type.value,
            cardholder_name=deactivated_card.cardholder_name,
            expiry_date=deactivated_card.expiry_date,
            status=deactivated_card.status.value,
            is_contactless=deactivated_card.is_contactless,
            daily_limit=deactivated_card.daily_limit,
            created_at=deactivated_card.created_at,
            activated_at=deactivated_card.activated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{card_id}/limit", response_model=CardResponse)
async def update_card_limit(
    card_id: int,
    limit_data: CardLimitUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update card daily spending limit"""
    card = CardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    # Authorization check
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    account = AccountService.get_account_by_id(db, card.account_id)
    
    if not holder or not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this card"
        )
    
    try:
        updated_card = CardService.update_daily_limit(db, card_id, limit_data.new_limit)
        
        return CardResponse(
            id=updated_card.id,
            account_id=updated_card.account_id,
            card_number_masked=CardService.mask_card_number(updated_card.card_number),
            card_type=updated_card.card_type.value,
            cardholder_name=updated_card.cardholder_name,
            expiry_date=updated_card.expiry_date,
            status=updated_card.status.value,
            is_contactless=updated_card.is_contactless,
            daily_limit=updated_card.daily_limit,
            created_at=updated_card.created_at,
            activated_at=updated_card.activated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

