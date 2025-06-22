from sqlalchemy import Boolean, Column, Integer, String, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)
    is_active = Column(Boolean, default=True)

class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    full_name = Column(String)
    bio = Column(String, nullable=True)
    skills = Column(String, nullable=True)  # Comma-separated skills
    portfolio_url = Column(String, nullable=True)
    is_freelancer = Column(Boolean, default=False)
    is_client = Column(Boolean, default=False) 