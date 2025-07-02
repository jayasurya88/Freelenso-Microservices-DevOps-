from sqlalchemy.orm import Session
from passlib.context import CryptContext
from . import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = get_user(db, user_id)
    for key, value in user.dict(exclude_unset=True).items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_profile(db: Session, user_id: int):
    return db.query(models.UserProfile).filter(models.UserProfile.user_id == user_id).first()

def create_user_profile(db: Session, profile: schemas.UserProfileCreate):
    db_profile = models.UserProfile(**profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def update_user_profile(db: Session, user_id: int, profile: schemas.UserProfileUpdate):
    db_profile = get_user_profile(db, user_id)
    for key, value in profile.dict(exclude_unset=True).items():
        setattr(db_profile, key, value)
    db.commit()
    db.refresh(db_profile)
    return db_profile 