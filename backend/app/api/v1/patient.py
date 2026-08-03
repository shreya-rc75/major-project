from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.patient_service import PatientService
from app.schemas.patient_schemas import PatientProfile, AnalysisHistoryEntry, ReportEntry, RiskEntry, NotificationOut
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/patient", tags=["patient"])

# auth placeholder
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


def require_patient(user = Depends(_get_current_user)):
    if not user or user.get("role") != "patient":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patient role required")
    return user


@router.get("/profile", response_model=PatientProfile)
def get_profile(db: Session = Depends(get_db), user = Depends(require_patient)):
    svc = PatientService(db)
    try:
        profile = svc.profile(user.get("patient_id") or user.get("id"))
        return profile
    except Exception as exc:
        logger.exception("Failed to get patient profile: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/history", response_model=List[AnalysisHistoryEntry])
def get_history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), user = Depends(require_patient)):
    svc = PatientService(db)
    pid = user.get("patient_id") or user.get("id")
    try:
        return svc.history(pid, limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Failed to get history: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/reports", response_model=List[ReportEntry])
def get_reports(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), user = Depends(require_patient)):
    svc = PatientService(db)
    pid = user.get("patient_id") or user.get("id")
    try:
        return svc.reports(pid, limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Failed to fetch reports: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/risk-history", response_model=List[RiskEntry])
def get_risk_history(db: Session = Depends(get_db), user = Depends(require_patient)):
    svc = PatientService(db)
    pid = user.get("patient_id") or user.get("id")
    try:
        return svc.risk_history(pid)
    except Exception as exc:
        logger.exception("Failed to fetch risk history: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/notifications", response_model=List[NotificationOut])
def get_notifications(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), user = Depends(require_patient)):
    svc = PatientService(db)
    pid = user.get("patient_id") or user.get("id")
    try:
        return svc.notifications(pid, limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Failed to fetch notifications: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/reports/download/{report_id}")
def download_report(report_id: int, db: Session = Depends(get_db), user = Depends(require_patient)):
    svc = PatientService(db)
    pid = user.get("patient_id") or user.get("id")
    try:
        res = svc.download_report(pid, report_id)
        return Response(content=res["bytes"], media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={res['filename']}"})
    except Exception as exc:
        logger.exception("Failed to download report: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
