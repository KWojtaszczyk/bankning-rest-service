from sqlalchemy.orm import Session
from app.models.card import Card, CardType, CardStatus
from app.models.account import Account
from app.schemas.card import CardCreate
from typing import List, Optional, Tuple
from decimal import Decimal
import random
import hashlib
from datetime import date, datetime, timezone, timedelta

class CardService:
    """Service for managing bank cards"""
    
    @staticmethod
    def _generate_card_number() -> str:
        """
        Generate a valid-looking 16-digit card number.
        
        NOTE: This is a simplified implementation for MVP/testing.
        Production systems should:
        - Implement Luhn algorithm for valid card numbers
        - Use a proper card number generation service
        - Follow PCI DSS compliance standards
        """
        # Format: 4xxx-xxxx-xxxx-xxxx (Visa-like format)
        # First digit 4 for Visa, 5 for Mastercard, etc.
        first_digit = random.choice(['4', '5'])
        remaining_digits = ''.join([str(random.randint(0, 9)) for _ in range(15)])
        card_number = first_digit + remaining_digits
        
        # Format with spaces: xxxx xxxx xxxx xxxx
        return f"{card_number[0:4]} {card_number[4:8]} {card_number[8:12]} {card_number[12:16]}"
    
    @staticmethod
    def _generate_cvv() -> str:
        """Generate a 3-digit CVV"""
        return ''.join([str(random.randint(0, 9)) for _ in range(3)])
    
    @staticmethod
    def _hash_sensitive_data(data: str) -> str:
        """Hash sensitive data (PIN, CVV)"""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _mask_card_number(card_number: str) -> str:
        """Mask card number to show only last 4 digits"""
        # Remove spaces for processing
        clean_number = card_number.replace(' ', '')
        # Return format: **** **** **** 1234
        return f"**** **** **** {clean_number[-4:]}"
    
    @staticmethod
    def _calculate_expiry_date() -> date:
        """Calculate card expiry date (3 years from now)"""
        today = datetime.now(timezone.utc).date()
        return date(today.year + 3, today.month, 1)  # First day of month, 3 years ahead
    
    @staticmethod
    def create_card(
        db: Session,
        card_data: CardCreate,
        account_holder_id: int
    ) -> Tuple[Card, str, str]:
        """
        Create a new card linked to an account
        Returns: (Card object, full_card_number, cvv)
        """
        # Verify account exists and belongs to account holder
        account = db.query(Account).filter(Account.id == card_data.account_id).first()
        if not account:
            raise ValueError("Account not found")
        
        if account.account_holder_id != account_holder_id:
            raise ValueError("Account does not belong to this account holder")
        
        # Validate card type
        if card_data.card_type not in [t.value for t in CardType]:
            raise ValueError(f"Invalid card type. Must be one of: {[t.value for t in CardType]}")
        
        # Generate card details
        card_number = CardService._generate_card_number()
        cvv = CardService._generate_cvv()
        expiry_date = CardService._calculate_expiry_date()
        
        # Hash sensitive data
        cvv_hash = CardService._hash_sensitive_data(cvv)
        pin_hash = CardService._hash_sensitive_data(card_data.pin)
        
        # ⚠️ SECURITY WARNING: Card numbers stored in PLAIN TEXT
        # PRODUCTION REQUIREMENTS:
        # 1. Encrypt card numbers using AES-256 or similar
        # 2. Use a key management service (AWS KMS, Azure Key Vault, etc.)
        # 3. Consider tokenization services (e.g., Stripe, Adyen)
        # 4. Implement PCI DSS Level 1 compliance
        # 5. Store encryption keys separately from database
        
        db_card = Card(
            account_id=card_data.account_id,
            card_number=card_number,  # ⚠️ PLAIN TEXT - ENCRYPT IN PRODUCTION!
            card_type=CardType(card_data.card_type),
            cardholder_name=card_data.cardholder_name,
            expiry_date=expiry_date,
            cvv_hash=cvv_hash,
            status=CardStatus.INACTIVE,  # Cards start inactive
            is_contactless=card_data.is_contactless,
            daily_limit=card_data.daily_limit
        )
        
        # DESIGN NOTE: Storing CVV and PIN hashes in single field
        # This is a simplified approach for MVP. In production:
        # - Add separate 'pin_hash' column to Card model
        # - Store PIN in a separate secure table with HSM backing
        # - Never store CVV (it should only be used for verification)
        db_card.cvv_hash = f"CVV:{cvv_hash}|PIN:{pin_hash}"
        
        db.add(db_card)
        db.commit()
        db.refresh(db_card)
        
        # Return card object with full number and CVV (only shown once)
        return db_card, card_number, cvv
    
    @staticmethod
    def get_card_by_id(db: Session, card_id: int) -> Optional[Card]:
        """Get card by ID"""
        return db.query(Card).filter(Card.id == card_id).first()
    
    @staticmethod
    def get_cards_by_account(db: Session, account_id: int) -> List[Card]:
        """Get all cards for an account"""
        return db.query(Card).filter(Card.account_id == account_id).all()
    
    @staticmethod
    def get_cards_by_holder(db: Session, account_holder_id: int) -> List[Card]:
        """Get all cards for an account holder (across all their accounts)"""
        return db.query(Card).join(Account).filter(
            Account.account_holder_id == account_holder_id
        ).all()
    
    @staticmethod
    def activate_card(db: Session, card_id: int, pin: str) -> Optional[Card]:
        """Activate a card with PIN verification"""
        card = db.query(Card).filter(Card.id == card_id).first()
        if not card:
            return None
        
        if card.status != CardStatus.INACTIVE:
            raise ValueError(f"Card is already {card.status.value}")
        
        # Verify PIN
        pin_hash = CardService._hash_sensitive_data(pin)
        stored_hashes = card.cvv_hash.split('|')
        stored_pin_hash = stored_hashes[1].replace('PIN:', '') if len(stored_hashes) > 1 else None
        
        if stored_pin_hash != pin_hash:
            raise ValueError("Invalid PIN")
        
        # Activate card
        card.status = CardStatus.ACTIVE
        card.activated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(card)
        return card
    
    @staticmethod
    def deactivate_card(db: Session, card_id: int, reason: str = "user_request") -> Optional[Card]:
        """Deactivate/block a card"""
        card = db.query(Card).filter(Card.id == card_id).first()
        if not card:
            return None
        
        if card.status == CardStatus.BLOCKED:
            raise ValueError("Card is already blocked")
        
        card.status = CardStatus.BLOCKED
        db.commit()
        db.refresh(card)
        return card
    
    @staticmethod
    def update_daily_limit(db: Session, card_id: int, new_limit: Decimal) -> Optional[Card]:
        """Update card daily spending limit"""
        card = db.query(Card).filter(Card.id == card_id).first()
        if not card:
            return None
        
        if new_limit < 0:
            raise ValueError("Daily limit cannot be negative")
        
        card.daily_limit = new_limit
        db.commit()
        db.refresh(card)
        return card
    
    @staticmethod
    def mask_card_number(card_number: str) -> str:
        """Public method to mask card numbers"""
        return CardService._mask_card_number(card_number)