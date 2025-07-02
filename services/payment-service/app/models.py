from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False)  # Reference to User Service
    balance = Column(Numeric(10, 2), default=0.00)
    escrow_balance = Column(Numeric(10, 2), default=0.00)
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = relationship("Transaction", back_populates="wallet")
    escrow_records = relationship("EscrowRecord", back_populates="wallet")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    transaction_id = Column(String(50), unique=True, index=True)
    amount = Column(Numeric(10, 2))
    transaction_type = Column(String(20))  # deposit, withdrawal, escrow, release, refund
    payment_method = Column(String(20))  # wallet, bank, card
    status = Column(String(20), default="pending")  # pending, completed, failed
    description = Column(Text)
    project_id = Column(Integer, nullable=True)  # Reference to Project Service
    milestone_id = Column(Integer, nullable=True)  # Reference to Project Service
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")

class EscrowRecord(Base):
    __tablename__ = "escrow_records"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    project_id = Column(Integer, nullable=False)  # Reference to Project Service
    milestone_id = Column(Integer, nullable=False)  # Reference to Project Service
    amount = Column(Numeric(10, 2))
    status = Column(String(20), default="active")  # active, released, refunded
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)

    # Relationships
    wallet = relationship("Wallet", back_populates="escrow_records")

class WithdrawalRequest(Base):
    __tablename__ = "withdrawal_requests"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"))
    amount = Column(Numeric(10, 2))
    payment_method = Column(String(20))  # bank, upi, card
    status = Column(String(20), default="pending")  # pending, processing, completed, rejected
    bank_details = Column(Text, nullable=True)  # JSON string of bank details
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    wallet = relationship("Wallet") 