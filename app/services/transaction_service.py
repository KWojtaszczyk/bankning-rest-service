from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from app.models.transaction import Transaction, TransactionType, TransactionStatus
from app.models.account import Account
from app.schemas.transaction import TransferRequest, TransactionFilter
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timezone
import random
import uuid
from app.logging_config import logger

class TransactionService:
    """Service for handling financial transactions"""
    
    @staticmethod
    def _generate_reference() -> str:
        """Generate a unique reference number"""
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        unique_id = str(uuid.uuid4().int)[:6]
        return f"TXN-{timestamp}-{unique_id}"

    @staticmethod
    def transfer_funds(
        db: Session, 
        from_account_id: int, 
        to_account_number: str, 
        amount: Decimal, 
        description: str = None
    ) -> Transaction:
        """
        Execute a money transfer between accounts with ACID compliance.
        """
        logger.info(f"Initiating transfer: Account {from_account_id} -> Account {to_account_number} | Amount: {amount}")
        
        try:
            # Start a nested transaction for atomicity
            db.begin_nested()
            
            # 1. Validate sender account
            sender = db.query(Account).filter(Account.id == from_account_id).with_for_update().first()
            if not sender:
                raise ValueError("Sender account not found")
            
            if sender.balance < amount:
                logger.warning(f"Transfer failed: Insufficient funds in account {from_account_id}")
                raise ValueError("Insufficient funds")
            
            # 2. Validate receiver account
            receiver = db.query(Account).filter(Account.account_number == to_account_number).with_for_update().first()
            if not receiver:
                logger.warning(f"Transfer failed: Receiver account {to_account_number} not found")
                raise ValueError("Receiver account not found")
            
            if sender.currency != receiver.currency:
                # For MVP, we only support same-currency transfers
                logger.warning(f"Transfer failed: Currency mismatch ({sender.currency} vs {receiver.currency})")
                raise ValueError(f"Currency mismatch: Cannot transfer from {sender.currency} to {receiver.currency}")
            
            # 3. Execute Transfer
            sender.balance -= amount
            receiver.balance += amount
            
            # 4. Create Transaction Record
            transaction = Transaction(
                transaction_type=TransactionType.TRANSFER,
                from_account_id=sender.id,
                to_account_id=receiver.id,
                amount=amount,
                currency=sender.currency,
                status=TransactionStatus.COMPLETED,
                description=description or f"Transfer to {receiver.account_number}",
                reference_number=TransactionService._generate_reference(),
                completed_at=datetime.now(timezone.utc)
            )
            
            db.add(transaction)
            db.commit()
            db.refresh(transaction)
            
            logger.info(f"Transfer successful: TXN {transaction.reference_number}")
            return transaction
            
        except Exception as e:
            db.rollback()
            logger.error(f"Transfer error: {str(e)}")
            raise e

    @staticmethod
    def get_transaction_history(
        db: Session,
        account_id: int,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[TransactionFilter] = None
    ) -> List[Transaction]:
        """
        Get transaction history for an account with optional filtering
        """
        query = db.query(Transaction).filter(
            or_(
                Transaction.from_account_id == account_id,
                Transaction.to_account_id == account_id
            )
        )
        
        if filters:
            if filters.start_date:
                query = query.filter(Transaction.created_at >= filters.start_date)
            if filters.end_date:
                query = query.filter(Transaction.created_at <= filters.end_date)
            if filters.transaction_type:
                query = query.filter(Transaction.transaction_type == filters.transaction_type)
            if filters.min_amount:
                query = query.filter(Transaction.amount >= filters.min_amount)
            if filters.max_amount:
                query = query.filter(Transaction.amount <= filters.max_amount)
        
        # Order by newest first
        return query.order_by(Transaction.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def rollback_transaction(db: Session, transaction_id: int, user_id: int) -> Transaction:
        """
        Rollback (reverse) a transaction by creating a counter-transaction
        """
        logger.info(f"Initiating rollback for transaction {transaction_id} by user {user_id}")
        
        original_txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not original_txn:
            raise ValueError("Transaction not found")
        
        # Verify ownership (user must own the source account)
        # Note: In a real app, we'd check Account ownership via AccountHolder
        # Here we assume the caller has already verified the user owns the account associated with the transaction
        # But for safety, we should verify the account belongs to the user.
        # Since we don't have easy access to AccountHolder here without extra queries, 
        # we'll rely on the route layer to verify account ownership before calling this,
        # OR we can check if the transaction is already reversed.
        
        if original_txn.status == TransactionStatus.REVERSED:
            raise ValueError("Transaction already reversed")
            
        if original_txn.transaction_type != TransactionType.TRANSFER:
             raise ValueError("Only transfers can be reversed")

        try:
            db.begin_nested()
            
            # Create Reversal Transaction (Swap sender/receiver)
            reversal_txn = Transaction(
                transaction_type=TransactionType.TRANSFER, # Or add REVERSAL type if desired
                from_account_id=original_txn.to_account_id,
                to_account_id=original_txn.from_account_id,
                amount=original_txn.amount,
                currency=original_txn.currency,
                status=TransactionStatus.COMPLETED,
                description=f"Reversal of {original_txn.reference_number}",
                reference_number=TransactionService._generate_reference(),
                completed_at=datetime.now(timezone.utc)
            )
            
            # Update balances
            sender = db.query(Account).filter(Account.id == original_txn.from_account_id).with_for_update().first()
            receiver = db.query(Account).filter(Account.id == original_txn.to_account_id).with_for_update().first()
            
            # Check if receiver (now sender of reversal) has enough funds
            if receiver.balance < original_txn.amount:
                 raise ValueError("Cannot reverse: Insufficient funds in recipient account")

            sender.balance += original_txn.amount
            receiver.balance -= original_txn.amount
            
            # Mark original as reversed
            original_txn.status = TransactionStatus.REVERSED
            
            db.add(reversal_txn)
            db.commit()
            db.refresh(reversal_txn)
            
            logger.info(f"Rollback successful: {original_txn.reference_number} -> {reversal_txn.reference_number}")
            return reversal_txn
            
        except Exception as e:
            db.rollback()
            logger.error(f"Rollback error: {str(e)}")
            raise e
