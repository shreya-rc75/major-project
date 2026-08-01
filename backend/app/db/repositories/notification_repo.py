from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.notification import Notification


def list_notifications_for_user(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def create_notification(db: Session, notification_in: dict) -> Notification:
    n = Notification(**notification_in)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def mark_notification_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def delete_notification(db: Session, notification: Notification) -> None:
    db.delete(notification)
    db.commit()
