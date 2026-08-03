from fastapi import APIRouter, Depends, HTTPException, status, Response
from typing import List
from sqlalchemy.orm import Session
from app.services.report_service import ReportService
from app.db.session import get_db
from app.db.repositories.report_repo import get_report, get_reports_by_patient
from app.schemas.report_schemas import ReportOut
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

# Dependency placeholder for JWT auth - import your project's dependency here
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        # Simple placeholder for environments without auth; override in tests
        return None


@router.post("/generate/{analysis_id}", response_model=ReportOut)
def generate_report_endpoint(analysis_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ReportService(db)
    try:
        result = svc.generate_report(analysis_id)
    except Exception as exc:
        logger.exception("Report generation failed for analysis %s", analysis_id)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
    # result contains {'report': <Report ORM>, 'path': rel_path}
    report = result.get("report")
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report_endpoint(report_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    rep = get_report(db, report_id)
    if not rep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return rep


@router.get("/download/{report_id}")
def download_report(report_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    rep = get_report(db, report_id)
    if not rep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    # Use LocalFileStorage to read file bytes and return as response
    from app.services.storage_service import LocalFileStorage
    storage = LocalFileStorage()
    try:
        file_bytes = storage.read_file(rep.pdf_path)
    except Exception as exc:
        logger.exception("Failed to read report file %s: %s", rep.pdf_path, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to read report file")
    return Response(content=file_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{report_id}.pdf"})


@router.get("/patient/{patient_id}", response_model=List[ReportOut])
def list_reports_by_patient(patient_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    reps = get_reports_by_patient(db, patient_id)
    return reps
