from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas

# Project CRUD operations
def get_project(db: Session, project_id: int):
    return db.query(models.Project).filter(models.Project.id == project_id).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Project).offset(skip).limit(limit).all()

def get_user_projects(db: Session, user_id: int, role: str = "client"):
    if role == "client":
        return db.query(models.Project).filter(models.Project.client_id == user_id).all()
    else:
        return db.query(models.Project).filter(models.Project.freelancer_id == user_id).all()

def create_project(db: Session, project: schemas.ProjectCreate):
    db_project = models.Project(
        title=project.title,
        description=project.description,
        budget=project.budget,
        client_id=project.client_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def update_project(db: Session, project_id: int, project: schemas.ProjectUpdate):
    db_project = get_project(db, project_id)
    for key, value in project.dict(exclude_unset=True).items():
        setattr(db_project, key, value)
    db_project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_project)
    return db_project

# Milestone CRUD operations
def get_milestone(db: Session, milestone_id: int):
    return db.query(models.ProjectMilestone).filter(models.ProjectMilestone.id == milestone_id).first()

def get_project_milestones(db: Session, project_id: int):
    return db.query(models.ProjectMilestone).filter(models.ProjectMilestone.project_id == project_id).all()

def create_milestone(db: Session, milestone: schemas.MilestoneCreate):
    db_milestone = models.ProjectMilestone(**milestone.dict())
    db.add(db_milestone)
    
    # Update project total milestones
    project = get_project(db, milestone.project_id)
    project.total_milestones += 1
    
    db.commit()
    db.refresh(db_milestone)
    return db_milestone

def update_milestone(db: Session, milestone_id: int, milestone: schemas.MilestoneUpdate):
    db_milestone = get_milestone(db, milestone_id)
    
    # If status is being updated to 'completed', set completed_at
    if milestone.status == "completed" and db_milestone.status != "completed":
        milestone.completed_at = datetime.utcnow()
        
        # Update project completed milestones count
        project = get_project(db, db_milestone.project_id)
        project.completed_milestones += 1
    
    for key, value in milestone.dict(exclude_unset=True).items():
        setattr(db_milestone, key, value)
    
    db_milestone.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_milestone)
    return db_milestone

# Project Activity CRUD operations
def create_project_activity(db: Session, project_id: int, user_id: int, activity_type: str, description: str):
    db_activity = models.ProjectActivity(
        project_id=project_id,
        user_id=user_id,
        activity_type=activity_type,
        description=description
    )
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def get_project_activities(db: Session, project_id: int, skip: int = 0, limit: int = 50):
    return db.query(models.ProjectActivity)\
        .filter(models.ProjectActivity.project_id == project_id)\
        .order_by(models.ProjectActivity.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all() 