from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.db.models.risk_analysis import RiskAnalysis


def create_risk_analysis(db: Session, risk_in: Dict[str, Any]) -> RiskAnalysis:
    r = RiskAnalysis(
        analysis_id=risk_in["analysis_id"],
        risk_1y=risk_in.get("risk_1y"),
        risk_3y=risk_in.get("risk_3y"),
        risk_5y=risk_in.get("risk_5y"),
        risk_category=risk_in.get("risk_category"),
        confidence=risk_in.get("confidence"),
        recommendations=risk_in.get("recommendations"),
        contributing_factors=risk_in.get("contributing_factors"),
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def get_risk_by_analysis(db: Session, analysis_id: int) -> Optional[RiskAnalysis]:
    return db.query(RiskAnalysis).filter(RiskAnalysis.analysis_id == analysis_id).one_or_none()
