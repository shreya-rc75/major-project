from app.services.report_service import ReportService
from app.db.repositories.report_repo import get_report, get_reports_by_patient
from app.db.session import get_db
from app.db.repositories.report_repo import create_report
from app.services.storage_service import LocalFileStorage
from app.db.repositories.analysis_repo import get_analysis
from app.db.repositories.study_repo import get_study
from app.db.repositories.patient_repo import get_patient
from app.db.repositories.image_repo import get_image
from app.db.repositories.stage_prediction_repo import get_stage_by_analysis
from app.db.repositories.risk_repo import get_risk_by_analysis

# Extend ReportService.generate_report to orchestrate full flow
# Safely monkey-patch the class method to avoid merge conflicts.
original_generate = ReportService.generate_report


def generate_report_full(self, analysis_id: int) -> Dict[str, Any]:
    """
    Full orchestration: collect -> render -> generate PDF -> store -> create DB record
    """
    # 1 collect
    data = self._collect_report_data(analysis_id)
    # 2 render html
    html = self._render_html(data)
    # 3 generate pdf
    pdf_bytes = self._generate_pdf(html)
    # 4 store pdf
    pdf_rel = self._store_report(analysis_id, pdf_bytes)
    # 5 create report record
    report = self._create_report_record(analysis_id, pdf_rel, html_storage_path=None)
    return {"report": report, "path": pdf_rel}

setattr(ReportService, "generate_report", generate_report_full)
