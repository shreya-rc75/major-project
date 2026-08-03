from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models.report import Report


def create_report(db: Session, report_in: Dict[str, Any]) -> Report:
    r = Report(
        patient_id=report_in["patient_id"],
        analysis_id=report_in["analysis_id"],
        pdf_path=report_in["pdf_path"],
        html_path=report_in.get("html_path"),
        report_status=report_in.get("report_status", "created"),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_report(db: Session, report_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.id == report_id).one_or_none()


def get_reports_by_patient(db: Session, patient_id: int) -> List[Report]:
    return db.query(Report).filter(Report.patient_id == patient_id).order_by(Report.created_at.desc()).all()


def get_report_by_analysis(db: Session, analysis_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.analysis_id == analysis_id).one_or_none()


def update_report_status(db: Session, report: Report, status: str) -> Report:
    report.report_status = status
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
