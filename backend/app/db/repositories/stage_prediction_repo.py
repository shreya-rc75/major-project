from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.stage_prediction import StagePrediction


def create_stage_prediction(db: Session, stage_in: Dict[str, Any]) -> StagePrediction:
    sp = StagePrediction(
        analysis_id=stage_in["analysis_id"],
        stage=stage_in["stage"],
        confidence=stage_in.get("confidence"),
        explanation=stage_in.get("explanation"),
        contributing_factors=stage_in.get("contributing_factors"),
    )
    db.add(sp)
    db.commit()
    db.refresh(sp)
    return sp


def create_stage_prediction_no_commit(db: Session, stage_in: Dict[str, Any]) -> StagePrediction:
    sp = StagePrediction(
        analysis_id=stage_in["analysis_id"],
        stage=stage_in["stage"],
        confidence=stage_in.get("confidence"),
        explanation=stage_in.get("explanation"),
        contributing_factors=stage_in.get("contributing_factors"),
    )
    db.add(sp)
    db.flush()
    # do not commit here
    return sp


def get_stage_by_analysis(db: Session, analysis_id: int) -> Optional[StagePrediction]:
    return db.query(StagePrediction).filter(StagePrediction.analysis_id == analysis_id).one_or_none()
