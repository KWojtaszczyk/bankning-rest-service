from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.statement import StatementRequest, StatementResponse
from app.services.statement_service import StatementService
from app.services.account_holder_service import AccountHolderService
from app.services.account_service import AccountService
from app.middleware.auth import get_current_active_user
from app.models.user import User
import os

router = APIRouter()


@router.post("/accounts/{account_id}/statements", response_model=StatementResponse, status_code=status.HTTP_201_CREATED)
async def generate_statement(
    account_id: int,
    request: StatementRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new statement for an account
    
    Supports PDF and JSON formats.
    """
    # Verify account belongs to user
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create an account holder profile first"
        )
    
    account = AccountService.get_account_by_id(db, account_id)
    if not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not found or does not belong to you"
        )
    
    try:
        statement = StatementService.generate_statement(
            db,
            account_id,
            request.period_start,
            request.period_end,
            request.format
        )
        return statement
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/accounts/{account_id}/statements", response_model=List[StatementResponse])
async def list_statements(
    account_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all statements for an account"""
    # Verify account belongs to user
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    if not holder:
        return []
    
    account = AccountService.get_account_by_id(db, account_id)
    if not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not found or does not belong to you"
        )
    
    statements = StatementService.list_statements(db, account_id)
    return statements


@router.get("/statements/{statement_id}", response_model=StatementResponse)
async def get_statement(
    statement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get statement metadata by ID"""
    statement = StatementService.get_statement_by_id(db, statement_id)
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Verify statement belongs to user's account
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    account = AccountService.get_account_by_id(db, statement.account_id)
    
    if not holder or not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this statement"
        )
    
    return statement


@router.get("/statements/{statement_id}/download")
async def download_statement(
    statement_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Download statement file"""
    statement = StatementService.get_statement_by_id(db, statement_id)
    if not statement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement not found"
        )
    
    # Verify statement belongs to user's account
    holder = AccountHolderService.get_account_holder_by_user(db, current_user.id)
    account = AccountService.get_account_by_id(db, statement.account_id)
    
    if not holder or not account or account.account_holder_id != holder.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this statement"
        )
    
    # Check if file exists
    if not statement.file_path or not os.path.exists(statement.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Statement file not found"
        )
    
    # Determine media type
    media_type = "application/pdf" if statement.format.value == "pdf" else "application/json"
    
    return FileResponse(
        path=statement.file_path,
        media_type=media_type,
        filename=os.path.basename(statement.file_path)
    )
