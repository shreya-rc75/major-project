from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.analysis_result import AnalysisResult


def update_analysis_no_commit(db: Session, analysis: AnalysisResult, updates: dict) -> AnalysisResult:
    for k, v in updates.items():
        setattr(analysis, k, v)
    db.add(analysis)
    # flush to persist changes to DB within transaction but do not commit
    db.flush()
    db.refresh(analysis)
    return analysis
