from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.notification_service import NotificationService
from app.schemas.notification_schemas import NotificationOut, NotificationCreate
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])

# Auth placeholder
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


@router.get("/", response_model=List[NotificationOut])
def list_notifications(patient_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = NotificationService(db)
    try:
        return svc.get_notifications(patient_id=patient_id, limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Failed to list notifications: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/read/{notification_id}")
def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = NotificationService(db)
    try:
        n = svc.mark_read(notification_id)
        return {"success": True, "notification_id": n.id}
    except Exception as exc:
        logger.exception("Failed to mark notification read: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = NotificationService(db)
    try:
        svc.delete(notification_id)
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to delete notification: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/send")
def send_notification(payload: NotificationCreate, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = NotificationService(db)
    try:
        res = svc.send_notification(payload.patient_id, payload.title, payload.message, type=payload.type, priority=payload.priority, send_email=payload.send_email)
        return res
    except Exception as exc:
        logger.exception("Failed to send notification: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
