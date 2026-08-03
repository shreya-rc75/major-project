from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.doctor_service import DoctorService
from app.schemas.doctor_schemas import PatientListItem, PatientDetail, ReportReviewOut, ApprovePayload, CommentPayload
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/doctor", tags=["doctor"])

# auth placeholder
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


# role check
def require_doctor(user = Depends(_get_current_user)):
    if not user or user.get("role") != "doctor":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctor role required")
    return user


@router.get("/patients", response_model=List[PatientListItem])
def list_patients(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user = Depends(require_doctor)):
    svc = DoctorService(db)
    return svc.list_patients(limit=limit, offset=offset)


@router.get("/patient/{patient_id}", response_model=PatientDetail)
def get_patient(patient_id: int, db: Session = Depends(get_db), user = Depends(require_doctor)):
    svc = DoctorService(db)
    try:
        return svc.get_patient_detail(patient_id)
    except Exception as exc:
        logger.exception("Failed to fetch patient detail: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/reports", response_model=List[ReportReviewOut])
def list_reports(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db), user = Depends(require_doctor)):
    svc = DoctorService(db)
    r = svc.list_reports(limit=limit, offset=offset)
    # convert to ReviewOut where possible
    out = []
    from app.db.repositories.report_review_repo import get_review_by_report
    for rep in r:
        rev = get_review_by_report(db, rep.id)
        if rev:
            out.append(rev)
        else:
            # create a placeholder object-like dict
            out.append({
                "id": None,
                "report_id": rep.id,
                "doctor_id": None,
                "status": "unreviewed",
                "comment": None,
                "stage_review": None,
                "risk_review": None,
                "created_at": None,
                "updated_at": None,
            })
    return out


@router.post("/report/{report_id}/approve", response_model=ReportReviewOut)
def approve_report(report_id: int, payload: ApprovePayload, db: Session = Depends(get_db), user = Depends(require_doctor)):
    svc = DoctorService(db)
    doctor_id = user.get("id")
    try:
        rev = svc.approve_report(report_id, doctor_id, comment=payload.comment, stage_review=payload.stage_review, risk_review=payload.risk_review)
        return rev
    except Exception as exc:
        logger.exception("Failed to approve report: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/report/{report_id}/reject", response_model=ReportReviewOut)
def reject_report(report_id: int, payload: ApprovePayload, db: Session = Depends(get_db), user = Depends(require_doctor)):
    svc = DoctorService(db)
    doctor_id = user.get("id")
    try:
        rev = svc.reject_report(report_id, doctor_id, comment=payload.comment)
        return rev
    except Exception as exc:
        logger.exception("Failed to reject report: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/report/{report_id}/comment", response_model=ReportReviewOut)
def comment_report(report_id: int, payload: CommentPayload, db: Session = Depends(get_db), user = Depends(require_doctor)):
    svc = DoctorService(db)
    doctor_id = user.get("id")
    try:
        rev = svc.comment_report(report_id, doctor_id, payload.comment)
        return rev
    except Exception as exc:
        logger.exception("Failed to add comment to report: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
