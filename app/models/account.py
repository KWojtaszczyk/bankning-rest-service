from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import enum


class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    BUSINESS = "business"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_holder_id = Column(Integer, ForeignKey("account_holders.id"), nullable=False)
    account_number = Column(String, unique=True, index=True, nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    balance = Column(Numeric(precision=15, scale=2), default=0.00, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    status = Column(Enum(AccountStatus), default=AccountStatus.ACTIVE)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    account_holder = relationship("AccountHolder", back_populates="accounts")
    transactions_from = relationship("Transaction", foreign_keys="Transaction.from_account_id",
                                     back_populates="from_account")
    transactions_to = relationship("Transaction", foreign_keys="Transaction.to_account_id", back_populates="to_account")
    cards = relationship("Card", back_populates="account")
    statements = relationship("Statement", back_populates="account")


