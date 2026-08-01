from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.analysis_result import AnalysisResult


def get_analysis(db: Session, analysis_id: int) -> Optional[AnalysisResult]:
    return db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).one_or_none()


def list_analyses_by_study(db: Session, study_id: int, skip: int = 0, limit: int = 50) -> List[AnalysisResult]:
    return db.query(AnalysisResult).filter(AnalysisResult.study_id == study_id).order_by(AnalysisResult.created_at.desc()).offset(skip).limit(limit).all()


def create_analysis(db: Session, analysis_in: dict) -> AnalysisResult:
    analysis = AnalysisResult(**analysis_in)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def update_analysis(db: Session, analysis: AnalysisResult, updates: dict) -> AnalysisResult:
    for k, v in updates.items():
        setattr(analysis, k, v)
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def delete_analysis(db: Session, analysis: AnalysisResult) -> None:
    db.delete(analysis)
    db.commit()
