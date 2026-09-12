import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from . import models, schemas

def get_wallet_by_user_id(db: Session, user_id: int):
    return db.query(models.Wallet).filter(models.Wallet.user_id == user_id).first()

def get_wallet(db: Session, wallet_id: int):
    return db.query(models.Wallet).filter(models.Wallet.id == wallet_id).first()

def create_wallet(db: Session, wallet: schemas.WalletCreate):
    db_wallet = models.Wallet(
        user_id=wallet.user_id,
        balance=Decimal("0.00"),
        escrow_balance=Decimal("0.00"),
        currency=wallet.currency,
        is_active=True
    )
    db.add(db_wallet)
    db.commit()
    db.refresh(db_wallet)
    return db_wallet

def get_or_create_wallet(db: Session, user_id: int, currency: str = "USD"):
    wallet = get_wallet_by_user_id(db, user_id=user_id)
    if not wallet:
        wallet = models.Wallet(
            user_id=user_id,
            balance=Decimal("0.00"),
            escrow_balance=Decimal("0.00"),
            currency=currency,
            is_active=True
        )
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
    return wallet

def get_transactions(db: Session, wallet_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).filter(
        models.Transaction.wallet_id == wallet_id
    ).order_by(models.Transaction.created_at.desc()).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    tx_id = f"tx_{uuid.uuid4().hex[:12]}"
    db_transaction = models.Transaction(
        wallet_id=transaction.wallet_id,
        transaction_id=tx_id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        payment_method=transaction.payment_method,
        description=transaction.description,
        project_id=transaction.project_id,
        milestone_id=transaction.milestone_id,
        status="completed"
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def fund_milestone(db: Session, user_id: int, req: schemas.FundMilestoneRequest):
    wallet = get_or_create_wallet(db, user_id)
    amount = Decimal(str(req.amount))
    
    # Deduct from wallet balance and put into escrow
    wallet.balance = Decimal(str(wallet.balance)) - amount
    wallet.escrow_balance = Decimal(str(wallet.escrow_balance)) + amount
    
    # Create Escrow Record
    escrow = models.EscrowRecord(
        wallet_id=wallet.id,
        project_id=req.project_id,
        milestone_id=req.milestone_id,
        amount=amount,
        status="active"
    )
    db.add(escrow)
    
    # Create Transaction
    tx = models.Transaction(
        wallet_id=wallet.id,
        transaction_id=f"tx_escrow_{uuid.uuid4().hex[:10]}",
        amount=amount,
        transaction_type="escrow",
        payment_method="wallet",
        description=f"Funded milestone {req.milestone_id} for project {req.project_id}",
        project_id=req.project_id,
        milestone_id=req.milestone_id,
        status="completed"
    )
    db.add(tx)
    db.commit()
    db.refresh(escrow)
    return escrow

def release_milestone(db: Session, req: schemas.ReleaseMilestoneRequest):
    escrow = db.query(models.EscrowRecord).filter(
        models.EscrowRecord.project_id == req.project_id,
        models.EscrowRecord.milestone_id == req.milestone_id,
        models.EscrowRecord.status == "active"
    ).first()
    if not escrow:
        return None
    
    wallet = get_wallet(db, escrow.wallet_id)
    if wallet:
        wallet.escrow_balance = Decimal(str(wallet.escrow_balance)) - Decimal(str(escrow.amount))
    
    escrow.status = "released"
    escrow.released_at = datetime.utcnow()
    db.commit()
    db.refresh(escrow)
    return escrow

def create_withdrawal(db: Session, withdrawal: schemas.WithdrawalRequestCreate):
    wallet = get_wallet(db, withdrawal.wallet_id)
    if not wallet:
        return None
    
    req = models.WithdrawalRequest(
        wallet_id=withdrawal.wallet_id,
        amount=withdrawal.amount,
        payment_method=withdrawal.payment_method,
        bank_details=withdrawal.bank_details,
        status="pending"
    )
    db.add(req)
    wallet.balance = Decimal(str(wallet.balance)) - Decimal(str(withdrawal.amount))
    db.commit()
    db.refresh(req)
    return req