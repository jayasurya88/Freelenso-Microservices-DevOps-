from fastapi import FastAPI, Depends, HTTPException, WebSocket, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import json
import aioredis
from datetime import datetime
from . import models, schemas, crud
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Notification Service")

# Redis connection for real-time notifications
redis = aioredis.from_url("redis://redis:6379", decode_responses=True)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/notifications/", response_model=schemas.Notification)
async def create_notification(
    notification: schemas.NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Create notification in database
    db_notification = crud.create_notification(db=db, notification=notification)
    
    # Send real-time notification
    notification_data = {
        "id": db_notification.id,
        "type": notification.type,
        "message": notification.message,
        "created_at": db_notification.created_at.isoformat()
    }
    
    # Publish to Redis for WebSocket clients
    background_tasks.add_task(
        redis.publish,
        f"user:{notification.recipient_id}",
        json.dumps(notification_data)
    )
    
    return db_notification

@app.get("/api/notifications/user/{user_id}", response_model=List[schemas.Notification])
def read_user_notifications(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    notifications = crud.get_user_notifications(db, user_id=user_id, skip=skip, limit=limit)
    return notifications

@app.get("/api/notifications/user/{user_id}/unread", response_model=List[schemas.Notification])
def read_unread_notifications(user_id: int, db: Session = Depends(get_db)):
    return crud.get_unread_notifications(db, user_id=user_id)

@app.put("/api/notifications/{notification_id}/read", response_model=schemas.Notification)
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    db_notification = crud.mark_notification_read(db, notification_id=notification_id)
    if db_notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification

@app.put("/api/notifications/user/{user_id}/mark-all-read")
def mark_all_notifications_read(user_id: int, db: Session = Depends(get_db)):
    crud.mark_all_read(db, user_id=user_id)
    return {"status": "success"}

@app.get("/api/notifications/preferences/{user_id}", response_model=schemas.NotificationPreference)
def get_preferences(user_id: int, db: Session = Depends(get_db)):
    db_preferences = crud.get_notification_preferences(db, user_id=user_id)
    if db_preferences is None:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return db_preferences

@app.post("/api/notifications/preferences/", response_model=schemas.NotificationPreference)
def create_preferences(preferences: schemas.NotificationPreferenceCreate, db: Session = Depends(get_db)):
    db_preferences = crud.get_notification_preferences(db, user_id=preferences.user_id)
    if db_preferences:
        raise HTTPException(status_code=400, detail="Preferences already exist")
    return crud.create_notification_preferences(db=db, preferences=preferences)

@app.put("/api/notifications/preferences/{user_id}", response_model=schemas.NotificationPreference)
def update_preferences(
    user_id: int,
    preferences: schemas.NotificationPreferenceUpdate,
    db: Session = Depends(get_db)
):
    db_preferences = crud.update_notification_preferences(db, user_id=user_id, preferences=preferences)
    if db_preferences is None:
        raise HTTPException(status_code=404, detail="Preferences not found")
    return db_preferences

# WebSocket connection for real-time notifications
@app.websocket("/ws/notifications/{user_id}")
async def notifications_websocket(websocket: WebSocket, user_id: int):
    await websocket.accept()
    
    # Subscribe to user's notification channel
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"user:{user_id}")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                await websocket.send_text(message["data"])
    except:
        await websocket.close()
    finally:
        await pubsub.unsubscribe(f"user:{user_id}") 