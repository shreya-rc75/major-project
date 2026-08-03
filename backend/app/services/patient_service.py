from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.repositories.patient_portal_repo import PatientPortalRepo
import logging

logger = logging.getLogger(__name__)


class PatientService:
    """Business logic for patient-facing operations: profile, history, reports, notifications, risk trends."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = PatientPortalRepo(db)

    def profile(self, patient_id: int) -> Dict[str, Any]:
        patient = self.repo.get_patient_profile(patient_id)
        if not patient:
            raise RuntimeError("Patient not found")
        # mask PII as needed; return basic fields
        return {"id": patient.id, "patient_identifier": patient.patient_identifier, "full_name": patient.full_name, "created_at": getattr(patient, 'created_at', None)}

    def history(self, patient_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return self.repo.get_analysis_history(patient_id, limit=limit, offset=offset)

    def reports(self, patient_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        reps = self.repo.get_reports_for_patient(patient_id, limit=limit, offset=offset)
        out = []
        for r in reps:
            out.append({
                "id": r.id,
                "analysis_id": r.analysis_id,
                "pdf_path": r.pdf_path,
                "html_path": r.html_path,
                "status": r.report_status,
                "created_at": r.created_at,
            })
        return out

    def risk_history(self, patient_id: int) -> List[Dict[str, Any]]:
        return self.repo.get_risk_history(patient_id)

    def notifications(self, patient_id: int, limit: int = 50, offset: int = 0):
        return self.repo.get_notifications(patient_id, limit=limit, offset=offset)

    def download_report(self, patient_id: int, report_id: int) -> Dict[str, Any]:
        # ensure report belongs to patient
        from app.db.repositories.report_repo import get_report
        rpt = get_report(self.db, report_id)
        if not rpt or rpt.patient_id != patient_id:
            raise RuntimeError("Report not found for patient")
        from app.services.storage_service import LocalFileStorage
        storage = LocalFileStorage()
        data = storage.read_file(rpt.pdf_path)
        return {"bytes": data, "filename": f"report_{report_id}.pdf"}
