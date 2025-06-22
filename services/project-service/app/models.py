from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    client_id = Column(Integer, nullable=False)  # Reference to User Service
    freelancer_id = Column(Integer, nullable=True)  # Reference to User Service
    status = Column(String(20), default='open')  # open, in_progress, completed, cancelled
    budget = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_milestones = Column(Integer, default=0)
    total_milestones = Column(Integer, default=0)

    # Relationship with milestones
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")

class ProjectMilestone(Base):
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    title = Column(String(200), nullable=False)
    description = Column(Text)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default='pending')  # pending, funded, completed, approved, rejected
    due_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with project
    project = relationship("Project", back_populates="milestones")

class ProjectActivity(Base):
    __tablename__ = "project_activities"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(Integer, nullable=False)  # Reference to User Service
    activity_type = Column(String(50), nullable=False)  # milestone_created, milestone_completed, etc.
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with project
    project = relationship("Project") 