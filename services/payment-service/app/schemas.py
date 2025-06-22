from typing import Optional, List
from pydantic import BaseModel, condecimal
from datetime import datetime
from decimal import Decimal

class WalletBase(BaseModel):
    currency: str = "USD"

class WalletCreate(WalletBase):
    user_id: int

class Wallet(WalletBase):
    id: int
    user_id: int
    balance: condecimal(max_digits=10, decimal_places=2)
    escrow_balance: condecimal(max_digits=10, decimal_places=2)
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TransactionBase(BaseModel):
    amount: condecimal(max_digits=10, decimal_places=2)
    transaction_type: str
    payment_method: str
    description: str
    project_id: Optional[int] = None
    milestone_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    wallet_id: int

class Transaction(TransactionBase):
    id: int
    transaction_id: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class EscrowRecordBase(BaseModel):
    project_id: int
    milestone_id: int
    amount: condecimal(max_digits=10, decimal_places=2)

class EscrowRecordCreate(EscrowRecordBase):
    wallet_id: int

class EscrowRecord(EscrowRecordBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    released_at: Optional[datetime]

    class Config:
        orm_mode = True

class WithdrawalRequestBase(BaseModel):
    amount: condecimal(max_digits=10, decimal_places=2)
    payment_method: str
    bank_details: Optional[str] = None

class WithdrawalRequestCreate(WithdrawalRequestBase):
    wallet_id: int

class WithdrawalRequest(WithdrawalRequestBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    class Config:
        orm_mode = True

# API Request/Response Models
class FundMilestoneRequest(BaseModel):
    project_id: int
    milestone_id: int
    amount: condecimal(max_digits=10, decimal_places=2)

class ReleaseMilestoneRequest(BaseModel):
    project_id: int
    milestone_id: int

class WalletBalance(BaseModel):
    available_balance: condecimal(max_digits=10, decimal_places=2)
    escrow_balance: condecimal(max_digits=10, decimal_places=2)
    total_balance: condecimal(max_digits=10, decimal_places=2)
    currency: str 