from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from app.tasks.pipeline_tasks import _get_progress
from app.tasks.celery_app import celery_app
from app.db.session import get_db
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

# auth placeholder
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


@router.get("/status/{task_id}")
def get_task_status(task_id: str, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    progress = _get_progress(task_id)
    async_result = celery_app.AsyncResult(task_id)
    resp = {
        "task_id": task_id,
        "celery_state": async_result.state,
        "progress": progress,
    }
    return JSONResponse(resp)
