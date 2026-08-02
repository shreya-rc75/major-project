from typing import Dict, Any
from sqlalchemy.orm import Session
from app.ai.risk.risk_model import predict_risk
from app.db.repositories.risk_repo import create_risk_analysis


def predict_and_persist(db: Session, analysis_id: int, clinical_data: Dict[str, Any], image_probs: Dict[str, Any], per_cell_features: Any = None):
    # Run risk prediction
    result = predict_risk(clinical_data, image_probs, per_cell_features)
    # Persist to DB
    create_risk_analysis(db, {
        "analysis_id": analysis_id,
        "risk_1y": result.get("risk_1y"),
        "risk_3y": result.get("risk_3y"),
        "risk_5y": result.get("risk_5y"),
        "risk_category": result.get("risk_category"),
        "confidence": result.get("confidence"),
        "recommendations": result.get("recommendations"),
        "contributing_factors": result.get("contributing_factors"),
    })
    return result
