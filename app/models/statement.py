from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base
import enum


class StatementFormat(str, enum.Enum):
    PDF = "pdf"
    JSON = "json"


class Statement(Base):
    __tablename__ = "statements"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    statement_period_start = Column(Date, nullable=False)
    statement_period_end = Column(Date, nullable=False)
    format = Column(Enum(StatementFormat), nullable=False)
    file_path = Column(String, nullable=True)  # Path to generated file
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    account = relationship("Account", back_populates="statements")
