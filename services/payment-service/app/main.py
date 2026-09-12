from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
from . import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Payment Service")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Payment Service is running"}

@app.get("/api/payments/wallet/{user_id}", response_model=schemas.Wallet)
def get_user_wallet(user_id: int, db: Session = Depends(get_db)):
    wallet = crud.get_or_create_wallet(db, user_id=user_id)
    return wallet

@app.get("/api/payments/wallet/{user_id}/balance", response_model=schemas.WalletBalance)
def get_user_wallet_balance(user_id: int, db: Session = Depends(get_db)):
    wallet = crud.get_or_create_wallet(db, user_id=user_id)
    return schemas.WalletBalance(
        available_balance=wallet.balance,
        escrow_balance=wallet.escrow_balance,
        total_balance=wallet.balance + wallet.escrow_balance,
        currency=wallet.currency
    )

@app.post("/api/payments/transactions/", response_model=schemas.Transaction)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    return crud.create_transaction(db=db, transaction=transaction)

@app.get("/api/payments/transactions/{wallet_id}", response_model=List[schemas.Transaction])
def get_transactions(wallet_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_transactions(db=db, wallet_id=wallet_id, skip=skip, limit=limit)

@app.post("/api/payments/milestones/fund/", response_model=schemas.EscrowRecord)
def fund_milestone(user_id: int, request: schemas.FundMilestoneRequest, db: Session = Depends(get_db)):
    return crud.fund_milestone(db=db, user_id=user_id, req=request)

@app.post("/api/payments/milestones/release/", response_model=schemas.EscrowRecord)
def release_milestone(request: schemas.ReleaseMilestoneRequest, db: Session = Depends(get_db)):
    escrow = crud.release_milestone(db=db, req=request)
    if not escrow:
        raise HTTPException(status_code=404, detail="Active escrow record not found")
    return escrow

@app.post("/api/payments/withdraw/", response_model=schemas.WithdrawalRequest)
def withdraw_funds(withdrawal: schemas.WithdrawalRequestCreate, db: Session = Depends(get_db)):
    req = crud.create_withdrawal(db=db, withdrawal=withdrawal)
    if not req:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return req