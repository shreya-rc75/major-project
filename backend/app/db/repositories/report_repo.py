from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.report import Report


def get_report(db: Session, report_id: int) -> Optional[Report]:
    return db.query(Report).filter(Report.id == report_id).one_or_none()


def list_reports_by_study(db: Session, study_id: int, skip: int = 0, limit: int = 50):
    return db.query(Report).filter(Report.study_id == study_id).order_by(Report.created_at.desc()).offset(skip).limit(limit).all()


def create_report(db: Session, report_in: dict) -> Report:
    rpt = Report(**report_in)
    db.add(rpt)
    db.commit()
    db.refresh(rpt)
    return rpt


def update_report(db: Session, report: Report, updates: dict) -> Report:
    for k, v in updates.items():
        setattr(report, k, v)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def delete_report(db: Session, report: Report) -> None:
    db.delete(report)
    db.commit()
