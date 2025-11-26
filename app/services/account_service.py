from sqlalchemy.orm import Session
from app.models.account import Account, AccountType, AccountStatus
from app.models.account_holder import AccountHolder
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from typing import List, Optional
from decimal import Decimal
import random
import string
from datetime import datetime, timezone

class AccountService:
    """Service for managing bank accounts"""
    
    @staticmethod
    def generate_account_number() -> str:
        """Generate a unique 12-digit account number"""
        # Format: XXXX-XXXX-XXXX
        return ''.join(random.choices(string.digits, k=12))
    
    @staticmethod
    def create_account(
        db: Session, 
        account_holder_id: int, 
        account_type: str,
        initial_deposit: Decimal = Decimal('0.00'),
        currency: str = "USD"
    ) -> Account:
        """Create a new bank account"""
        # Verify account holder exists
        holder = db.query(AccountHolder).filter(AccountHolder.id == account_holder_id).first()
        if not holder:
            raise ValueError("Account holder not found")
        
        # Validate account type
        if account_type not in [t.value for t in AccountType]:
            raise ValueError(f"Invalid account type. Must be one of: {[t.value for t in AccountType]}")
        
        # Validate initial deposit
        if initial_deposit < 0:
            raise ValueError("Initial deposit cannot be negative")
        
        # Generate unique account number
        account_number = AccountService.generate_account_number()
        while db.query(Account).filter(Account.account_number == account_number).first():
            account_number = AccountService.generate_account_number()
        
        # Create account
        db_account = Account(
            account_holder_id=account_holder_id,
            account_number=account_number,
            account_type=AccountType(account_type),
            balance=initial_deposit,
            currency=currency,
            status=AccountStatus.ACTIVE
        )
        
        db.add(db_account)
        db.flush()  # Get the account ID without committing
        
        # If there's an initial deposit, create a transaction record
        if initial_deposit > 0:
            deposit_transaction = Transaction(
                transaction_type=TransactionType.DEPOSIT,
                to_account_id=db_account.id,
                amount=initial_deposit,
                currency=currency,
                status=TransactionStatus.COMPLETED,
                description="Initial deposit",
                reference_number=f"DEP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}",
                completed_at=datetime.now(timezone.utc)
            )
            db.add(deposit_transaction)
        
        db.commit()
        db.refresh(db_account)
        return db_account
    
    @staticmethod
    def get_account_by_id(db: Session, account_id: int) -> Optional[Account]:
        """Get account by ID"""
        return db.query(Account).filter(Account.id == account_id).first()
    
    @staticmethod
    def get_account_by_number(db: Session, account_number: str) -> Optional[Account]:
        """Get account by account number"""
        return db.query(Account).filter(Account.account_number == account_number).first()
    
    @staticmethod
    def get_accounts_by_holder(db: Session, account_holder_id: int) -> List[Account]:
        """Get all accounts for an account holder"""
        return db.query(Account).filter(Account.account_holder_id == account_holder_id).all()
    
    @staticmethod
    def get_account_balance(db: Session, account_id: int) -> Optional[Decimal]:
        """Get current account balance"""
        account = db.query(Account).filter(Account.id == account_id).first()
        return account.balance if account else None
    
    @staticmethod
    def update_account_status(db: Session, account_id: int, new_status: str) -> Optional[Account]:
        """Update account status (active, frozen, closed)"""
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return None
        
        if new_status not in [s.value for s in AccountStatus]:
            raise ValueError(f"Invalid status. Must be one of: {[s.value for s in AccountStatus]}")
        
        account.status = AccountStatus(new_status)
        db.commit()
        db.refresh(account)
        return account
