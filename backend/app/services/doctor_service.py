from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.repositories.report_repo import get_report, get_reports_by_patient
from app.db.repositories.analysis_repo import get_analyses_by_patient
from app.db.repositories.report_review_repo import create_review, get_review_by_report, update_review
from app.db.repositories.patient_repo import get_patient
import logging

logger = logging.getLogger(__name__)


class DoctorService:
    """Business logic for doctor portal: patients, reports, reviews, notes."""

    def __init__(self, db: Session):
        self.db = db

    def list_patients(self, limit: int = 50, offset: int = 0):
        # reuse patient repo list if available; otherwise simple query
        try:
            from app.db.repositories.patient_repo import list_patients
            return list_patients(self.db, limit=limit, offset=offset)
        except Exception:
            # fallback
            from app.db.models.patient import Patient
            return self.db.query(Patient).order_by(Patient.id).limit(limit).offset(offset).all()

    def get_patient_detail(self, patient_id: int) -> Dict[str, Any]:
        patient = get_patient(self.db, patient_id)
        if not patient:
            raise RuntimeError("Patient not found")
        # analyses and reports
        analyses = get_analyses_by_patient(self.db, patient_id)
        # for each analysis, gather reports
        reports = []
        for a in analyses:
            rpt = get_report(self.db, a.id)
            if rpt:
                reports.append(rpt)
        return {"patient": patient, "analyses": analyses, "reports": reports}

    def list_reports(self, limit: int = 50, offset: int = 0):
        # list all reports for doctors to review; reuse report repo
        try:
            from app.db.repositories.report_repo import list_reports
            return list_reports(self.db, limit=limit, offset=offset)
        except Exception:
            from app.db.models.report import Report
            return self.db.query(Report).order_by(Report.created_at.desc()).limit(limit).offset(offset).all()

    def approve_report(self, report_id: int, doctor_id: int, comment: Optional[str] = None, stage_review: Optional[str] = None, risk_review: Optional[str] = None):
        report = get_report(self.db, report_id)
        if not report:
            raise RuntimeError("Report not found")
        existing = get_review_by_report(self.db, report_id)
        if existing:
            updates = {"status": "approved", "doctor_id": doctor_id}
            if comment:
                updates["comment"] = comment
            if stage_review:
                updates["stage_review"] = stage_review
            if risk_review:
                updates["risk_review"] = risk_review
            return update_review(self.db, existing, updates)
        else:
            return create_review(self.db, {"report_id": report_id, "doctor_id": doctor_id, "status": "approved", "comment": comment, "stage_review": stage_review, "risk_review": risk_review})

    def reject_report(self, report_id: int, doctor_id: int, comment: Optional[str] = None):
        report = get_report(self.db, report_id)
        if not report:
            raise RuntimeError("Report not found")
        existing = get_review_by_report(self.db, report_id)
        if existing:
            return update_review(self.db, existing, {"status": "rejected", "doctor_id": doctor_id, "comment": comment})
        else:
            return create_review(self.db, {"report_id": report_id, "doctor_id": doctor_id, "status": "rejected", "comment": comment})

    def comment_report(self, report_id: int, doctor_id: int, comment: str):
        existing = get_review_by_report(self.db, report_id)
        if existing:
            # append comment
            prev = existing.comment or ""
            new_comment = prev + "\n" + comment if prev else comment
            return update_review(self.db, existing, {"comment": new_comment, "doctor_id": doctor_id})
        else:
            return create_review(self.db, {"report_id": report_id, "doctor_id": doctor_id, "status": "pending", "comment": comment})
