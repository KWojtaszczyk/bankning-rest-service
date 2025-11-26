from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Enum, Boolean, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import enum


class CardType(str, enum.Enum):
    DEBIT = "debit"
    CREDIT = "credit"
    VIRTUAL = "virtual"


class CardStatus(str, enum.Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXPIRED = "expired"


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    card_number = Column(String, unique=True, nullable=False)  # Last 4 digits stored, rest masked
    card_type = Column(Enum(CardType), nullable=False)
    cardholder_name = Column(String, nullable=False)
    expiry_date = Column(Date, nullable=False)
    cvv_hash = Column(String)  # Hashed CVV for security
    status = Column(Enum(CardStatus), default=CardStatus.INACTIVE)
    is_contactless = Column(Boolean, default=True)
    daily_limit = Column(Numeric(precision=15, scale=2), default=1000.00)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    activated_at = Column(DateTime)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    account = relationship("Account", back_populates="cards")
