from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AccountHolder(Base):
    __tablename__ = "account_holders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    phone_number = Column(String)
    address = Column(String)
    city = Column(String)
    country = Column(String)
    postal_code = Column(String)

    # KYC fields
    identification_type = Column(String)  # passport, drivers_license, national_id
    identification_number = Column(String)
    kyc_verified = Column(String, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="account_holder")
    accounts = relationship("Account", back_populates="account_holder")

