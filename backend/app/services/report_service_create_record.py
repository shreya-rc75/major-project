from typing import Any, Dict
from sqlalchemy.orm import Session
from app.services.report_service import ReportService
from app.db.repositories.report_repo import create_report
from app.db.repositories.patient_repo import get_patient
from app.db.repositories.analysis_repo import get_analysis
import logging

logger = logging.getLogger(__name__)


def _create_report_record(self, analysis_id: int, pdf_storage_path: str, html_storage_path: str | None = None) -> Any:
    """
    Persist a Report DB record linking the stored PDF to the analysis and patient.

    Returns the created Report ORM object.
    """
    # validate analysis exists
    analysis = get_analysis(self.db, analysis_id)
    if not analysis:
        logger.error("Cannot create report record: analysis %s not found", analysis_id)
        raise RuntimeError("Analysis not found for report creation")

    # determine patient id via study
    study = getattr(analysis, "study_id", None)
    patient_id = None
    if study:
        try:
            st = self.db.query("study").filter_by(id=study).first()
        except Exception:
            st = None
        # prefer repository function if available
        from app.db.repositories.study_repo import get_study
        stud = get_study(self.db, study)
        if stud:
            patient_id = getattr(stud, "patient_id", None)

    if not patient_id:
        logger.error("Cannot determine patient_id for analysis %s", analysis_id)
        raise RuntimeError("Patient not found for analysis when creating report")

    report = create_report(self.db, {
        "patient_id": patient_id,
        "analysis_id": analysis_id,
        "pdf_path": pdf_storage_path,
        "html_path": html_storage_path,
        "report_status": "created",
    })
    return report
