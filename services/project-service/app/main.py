from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import requests
from . import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Service")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/projects/", response_model=schemas.Project)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    # Verify client exists by calling User Service
    try:
        response = requests.get(f"http://user-service:8000/api/users/{project.client_id}")
        response.raise_for_status()
    except:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return crud.create_project(db=db, project=project)

@app.get("/api/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project

@app.get("/api/projects/", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    projects = crud.get_projects(db, skip=skip, limit=limit)
    return projects

@app.get("/api/projects/user/{user_id}", response_model=List[schemas.Project])
def read_user_projects(user_id: int, role: str = "client", db: Session = Depends(get_db)):
    projects = crud.get_user_projects(db, user_id=user_id, role=role)
    return projects

@app.put("/api/projects/{project_id}", response_model=schemas.Project)
def update_project(project_id: int, project: schemas.ProjectUpdate, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.update_project(db=db, project_id=project_id, project=project)

@app.post("/api/projects/{project_id}/milestones/", response_model=schemas.Milestone)
def create_milestone(
    project_id: int, 
    milestone: schemas.MilestoneCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_milestone = crud.create_milestone(db=db, milestone=milestone)
    
    # Create project activity
    background_tasks.add_task(
        crud.create_project_activity,
        db=db,
        project_id=project_id,
        user_id=db_project.client_id,
        activity_type="milestone_created",
        description=f"Created milestone: {milestone.title}"
    )
    
    # Notify freelancer if assigned
    if db_project.freelancer_id:
        try:
            requests.post(
                "http://notification-service:8000/api/notifications/",
                json={
                    "recipient_id": db_project.freelancer_id,
                    "type": "milestone_created",
                    "message": f"New milestone created for project: {db_project.title}"
                }
            )
        except:
            pass  # Don't fail if notification fails
    
    return db_milestone

@app.get("/api/projects/{project_id}/milestones/", response_model=List[schemas.Milestone])
def read_project_milestones(project_id: int, db: Session = Depends(get_db)):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_project_milestones(db=db, project_id=project_id)

@app.put("/api/projects/{project_id}/milestones/{milestone_id}", response_model=schemas.Milestone)
def update_milestone(
    project_id: int,
    milestone_id: int,
    milestone: schemas.MilestoneUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_milestone = crud.get_milestone(db, milestone_id=milestone_id)
    if db_milestone is None:
        raise HTTPException(status_code=404, detail="Milestone not found")
    if db_milestone.project_id != project_id:
        raise HTTPException(status_code=400, detail="Milestone does not belong to this project")
    
    updated_milestone = crud.update_milestone(db=db, milestone_id=milestone_id, milestone=milestone)
    
    # Create activity and notifications for status changes
    if milestone.status:
        activity_type = f"milestone_{milestone.status}"
        background_tasks.add_task(
            crud.create_project_activity,
            db=db,
            project_id=project_id,
            user_id=db_project.client_id,
            activity_type=activity_type,
            description=f"Milestone '{db_milestone.title}' status changed to {milestone.status}"
        )
        
        # Notify relevant users
        try:
            if milestone.status == "completed" and db_project.client_id:
                requests.post(
                    "http://notification-service:8000/api/notifications/",
                    json={
                        "recipient_id": db_project.client_id,
                        "type": "milestone_completed",
                        "message": f"Milestone completed for project: {db_project.title}"
                    }
                )
            elif milestone.status == "approved" and db_project.freelancer_id:
                requests.post(
                    "http://notification-service:8000/api/notifications/",
                    json={
                        "recipient_id": db_project.freelancer_id,
                        "type": "milestone_approved",
                        "message": f"Milestone approved for project: {db_project.title}"
                    }
                )
        except:
            pass  # Don't fail if notification fails
    
    return updated_milestone

@app.get("/api/projects/{project_id}/activities/", response_model=List[schemas.ProjectActivity])
def read_project_activities(
    project_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    db_project = crud.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return crud.get_project_activities(db=db, project_id=project_id, skip=skip, limit=limit) 