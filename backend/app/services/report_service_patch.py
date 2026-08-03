from app.services.report_service import ReportService
from app.db.repositories.report_repo import create_report, get_report
from app.db.repositories.study_repo import get_study
from app.db.repositories.analysis_repo import get_analysis
from app.db.repositories.patient_repo import get_patient
from app.db.repositories.image_repo import get_image
from app.db.repositories.stage_prediction_repo import get_stage_by_analysis
from app.db.repositories.risk_repo import get_risk_by_analysis
from app.db.repositories.report_repo import get_report as repo_get_report
from app.services.storage_service import LocalFileStorage
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

# Wire in the _create_report_record implementation into the ReportService class
# This avoids circular imports issues by attaching the implementation dynamically.
from app.services.report_service import ReportService as _RS

def _create_report_record_impl(self, analysis_id: int, pdf_storage_path: str, html_storage_path: str | None = None) -> Any:
    # validate analysis
    analysis = get_analysis(self.db, analysis_id)
    if not analysis:
        logger.error("Cannot create report record: analysis %s not found", analysis_id)
        raise RuntimeError("Analysis not found for report creation")
    # find patient id via study
    study = None
    if getattr(analysis, "study_id", None):
        study = get_study(self.db, analysis.study_id)
    if not study:
        logger.error("Study not found for analysis %s", analysis_id)
        raise RuntimeError("Study not found for report creation")
    patient = get_patient(self.db, study.patient_id)
    if not patient:
        logger.error("Patient not found for study %s", study.id)
        raise RuntimeError("Patient not found for report creation")

    report = create_report(self.db, {
        "patient_id": patient.id,
        "analysis_id": analysis_id,
        "pdf_path": pdf_storage_path,
        "html_path": html_storage_path,
        "report_status": "created",
    })
    return report

# attach implementation
setattr(_RS, "_create_report_record", _create_report_record_impl)
