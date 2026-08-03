from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.models.analysis_result import AnalysisResult
from app.db.models.report import Report
from app.db.models.risk_analysis import RiskAnalysis


class PatientPortalRepo:
    """Optimized queries for patient portal to avoid N+1 queries."""

    def __init__(self, db: Session):
        self.db = db

    def get_patient_profile(self, patient_id: int) -> Optional[Patient]:
        return self.db.query(Patient).filter(Patient.id == patient_id).one_or_none()

    def get_analysis_history(self, patient_id: int, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        # Join studies -> analyses -> images, order by analysis created_at desc
        q = (
            self.db.query(
                AnalysisResult.id.label("analysis_id"),
                AnalysisResult.created_at.label("analysis_date"),
                AnalysisResult.status,
                AnalysisResult.predicted_class,
                AnalysisResult.probabilities,
                Study.id.label("study_id"),
                Study.accession,
                Image.id.label("image_id"),
                Image.filename,
            )
            .join(Study, Study.id == AnalysisResult.study_id)
            .join(Image, Image.id == AnalysisResult.image_id)
            .filter(Study.patient_id == patient_id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        results = []
        for r in q.all():
            results.append({
                "analysis_id": r.analysis_id,
                "analysis_date": r.analysis_date,
                "status": r.status,
                "predicted_class": r.predicted_class,
                "probabilities": r.probabilities,
                "study_id": r.study_id,
                "accession": r.accession,
                "image_id": r.image_id,
                "filename": r.filename,
            })
        return results

    def get_reports_for_patient(self, patient_id: int, limit: int = 50, offset: int = 0) -> List[Report]:
        q = (
            self.db.query(Report)
            .filter(Report.patient_id == patient_id)
            .order_by(Report.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return q.all()

    def get_risk_history(self, patient_id: int) -> List[Dict[str, Any]]:
        # latest risk per analysis for this patient's studies
        subq = (
            self.db.query(
                RiskAnalysis.analysis_id.label("analysis_id"),
                func.max(RiskAnalysis.created_at).label("max_created")
            )
            .group_by(RiskAnalysis.analysis_id)
            .subquery()
        )
        q = (
            self.db.query(RiskAnalysis)
            .join(subq, (RiskAnalysis.analysis_id == subq.c.analysis_id) & (RiskAnalysis.created_at == subq.c.max_created))
            .join(AnalysisResult, AnalysisResult.id == RiskAnalysis.analysis_id)
            .join(Study, Study.id == AnalysisResult.study_id)
            .filter(Study.patient_id == patient_id)
            .order_by(RiskAnalysis.created_at.asc())
        )
        out = []
        for r in q.all():
            out.append({
                "analysis_id": r.analysis_id,
                "created_at": r.created_at,
                "risk_1y": r.risk_1y,
                "risk_3y": r.risk_3y,
                "risk_5y": r.risk_5y,
                "risk_category": r.risk_category,
            })
        return out

    def get_notifications(self, patient_id: int, limit: int = 50, offset: int = 0):
        from app.db.repositories.notification_repo import get_notifications_for_patient
        return get_notifications_for_patient(self.db, patient_id, limit=limit, offset=offset)

    def get_report_bytes(self, report_id: int) -> Optional[bytes]:
        rpt = self.db.query(Report).filter(Report.id == report_id).one_or_none()
        if not rpt:
            return None
        from app.services.storage_service import LocalFileStorage
        storage = LocalFileStorage()
        try:
            return storage.read_file(rpt.pdf_path)
        except Exception:
            return None
