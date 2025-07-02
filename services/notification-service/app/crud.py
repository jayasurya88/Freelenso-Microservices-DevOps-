from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas

def create_notification(db: Session, notification: schemas.NotificationCreate):
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_user_notifications(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(models.Notification)\
        .filter(models.Notification.recipient_id == user_id)\
        .order_by(models.Notification.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_unread_notifications(db: Session, user_id: int):
    return db.query(models.Notification)\
        .filter(
            models.Notification.recipient_id == user_id,
            models.Notification.is_read == False
        )\
        .order_by(models.Notification.created_at.desc())\
        .all()

def mark_notification_read(db: Session, notification_id: int):
    db_notification = db.query(models.Notification)\
        .filter(models.Notification.id == notification_id)\
        .first()
    if db_notification:
        db_notification.is_read = True
        db_notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(db_notification)
    return db_notification

def mark_all_read(db: Session, user_id: int):
    db.query(models.Notification)\
        .filter(
            models.Notification.recipient_id == user_id,
            models.Notification.is_read == False
        )\
        .update({
            models.Notification.is_read: True,
            models.Notification.read_at: datetime.utcnow()
        })
    db.commit()

def get_notification_preferences(db: Session, user_id: int):
    return db.query(models.NotificationPreference)\
        .filter(models.NotificationPreference.user_id == user_id)\
        .first()

def create_notification_preferences(db: Session, preferences: schemas.NotificationPreferenceCreate):
    db_preferences = models.NotificationPreference(**preferences.dict())
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences

def update_notification_preferences(db: Session, user_id: int, preferences: schemas.NotificationPreferenceUpdate):
    db_preferences = get_notification_preferences(db, user_id)
    if db_preferences:
        for key, value in preferences.dict(exclude_unset=True).items():
            setattr(db_preferences, key, value)
        db_preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_preferences)
    return db_preferences 