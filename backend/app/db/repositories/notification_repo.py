from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.notification import Notification


def create_notification(db: Session, notification_in: dict) -> Notification:
    n = Notification(
        patient_id=notification_in["patient_id"],
        title=notification_in["title"],
        message=notification_in["message"],
        type=notification_in.get("type", "info"),
        priority=notification_in.get("priority", "normal"),
    )
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def get_notifications_for_patient(db: Session, patient_id: int, limit: int = 50, offset: int = 0) -> List[Notification]:
    return db.query(Notification).filter(Notification.patient_id == patient_id).order_by(Notification.created_at.desc()).limit(limit).offset(offset).all()


def get_notification(db: Session, notification_id: int) -> Optional[Notification]:
    return db.query(Notification).filter(Notification.id == notification_id).one_or_none()


def mark_notification_as_read(db: Session, notification: Notification) -> Notification:
    notification.is_read = True
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def delete_notification(db: Session, notification: Notification) -> None:
    db.delete(notification)
    db.commit()
