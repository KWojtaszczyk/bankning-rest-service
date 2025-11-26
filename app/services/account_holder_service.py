from sqlalchemy.orm import Session
from app.models.account_holder import AccountHolder
from app.models.user import User
from app.schemas.account_holder import AccountHolderCreate, AccountHolderUpdate
from typing import Optional

class AccountHolderService:
    """Service for managing account holder profiles"""
    
    @staticmethod
    def create_account_holder(db: Session, user: User, holder_data: AccountHolderCreate) -> AccountHolder:
        """Create account holder profile for a user"""
        # Check if user already has an account holder profile
        existing = db.query(AccountHolder).filter(AccountHolder.user_id == user.id).first()
        if existing:
            raise ValueError("User already has an account holder profile")
        
        # Create new account holder
        db_holder = AccountHolder(
            user_id=user.id,
            first_name=holder_data.first_name,
            last_name=holder_data.last_name,
            date_of_birth=holder_data.date_of_birth,
            phone_number=holder_data.phone_number,
            address=holder_data.address,
            city=holder_data.city,
            country=holder_data.country,
            postal_code=holder_data.postal_code,
            identification_type=holder_data.identification_type,
            identification_number=holder_data.identification_number,
            kyc_verified=False  # Default to not verified
        )
        
        db.add(db_holder)
        db.commit()
        db.refresh(db_holder)
        return db_holder
    
    @staticmethod
    def get_account_holder_by_user(db: Session, user_id: int) -> Optional[AccountHolder]:
        """Get account holder profile by user ID"""
        return db.query(AccountHolder).filter(AccountHolder.user_id == user_id).first()
    
    @staticmethod
    def get_account_holder_by_id(db: Session, holder_id: int) -> Optional[AccountHolder]:
        """Get account holder profile by ID"""
        return db.query(AccountHolder).filter(AccountHolder.id == holder_id).first()
    
    @staticmethod
    def update_account_holder(db: Session, holder_id: int, holder_update: AccountHolderUpdate) -> Optional[AccountHolder]:
        """Update account holder profile"""
        db_holder = db.query(AccountHolder).filter(AccountHolder.id == holder_id).first()
        if not db_holder:
            return None
        
        # Update only provided fields
        update_data = holder_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_holder, field, value)
        
        db.commit()
        db.refresh(db_holder)
        return db_holder

