from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class ProjectBase(BaseModel):
    title: str
    description: str
    budget: Optional[float] = None

class ProjectCreate(ProjectBase):
    client_id: int

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    status: Optional[str] = None
    freelancer_id: Optional[int] = None

class MilestoneBase(BaseModel):
    title: str
    description: str
    amount: float
    due_date: Optional[datetime] = None

class MilestoneCreate(MilestoneBase):
    project_id: int

class MilestoneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    due_date: Optional[datetime] = None

class Milestone(MilestoneBase):
    id: int
    project_id: int
    status: str
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class Project(ProjectBase):
    id: int
    client_id: int
    freelancer_id: Optional[int]
    status: str
    completed_milestones: int
    total_milestones: int
    created_at: datetime
    updated_at: datetime
    milestones: List[Milestone] = []

    class Config:
        orm_mode = True

class ProjectActivity(BaseModel):
    id: int
    project_id: int
    user_id: int
    activity_type: str
    description: str
    created_at: datetime

    class Config:
        orm_mode = True 