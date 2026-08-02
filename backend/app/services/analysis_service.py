from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.repositories.analysis_repo import get_analysis, update_analysis
from fastapi import HTTPException, status
from app.ai.clinical.stage_estimator import estimate_stage
from app.db.repositories.stage_prediction_repo import create_stage_prediction


def run_analysis_and_persist(db: Session, analysis_id: int, model_inference_result: Dict[str, Any], clinical_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Persist inference outputs into AnalysisResult and return the updated record.
    model_inference_result expected keys: predicted_class, probabilities (dict), gradcam_bytes (optional), risk_score (optional), per_cell_features (optional)
    clinical_data: optional dict containing clinical inputs (hpv, biopsy, imaging, symptoms)
    """
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    updates = {
        "predicted_class": model_inference_result.get("predicted_class"),
        "probabilities": model_inference_result.get("probabilities"),
        "risk_score": model_inference_result.get("risk_score"),
        "status": "completed",
    }

    # Compute clinical stage using estimator and persist as separate StagePrediction record
    try:
        stage_result = estimate_stage(clinical_data, model_inference_result.get("probabilities", {}), model_inference_result.get("per_cell_features"))
        updates["clinical_stage"] = stage_result.get("stage")
        # Persist a dedicated StagePrediction record for auditability
        create_stage_prediction(db, stage_in={
            "analysis_id": analysis_id,
            "stage": stage_result.get("stage"),
            "confidence": stage_result.get("confidence"),
            "explanation": stage_result.get("explanation"),
            "contributing_factors": stage_result.get("contributing_factors"),
        })
    except Exception:
        updates["clinical_stage"] = None

    # handle gradcam bytes if present
    gradcam_bytes = model_inference_result.get("gradcam_bytes")
    if gradcam_bytes:
        from app.services.storage_service import LocalFileStorage
        from uuid import uuid4
        storage = LocalFileStorage()
        rel_path, size = storage.save_file(gradcam_bytes, filename=f"gradcam_{uuid4().hex}.png", subpath=f"studies/{analysis.study_id}/analysis")
        updates["gradcam_path"] = rel_path

    # Persist updates
    updated = update_analysis(db, analysis=analysis, updates=updates)
    return {"analysis_id": updated.id, "status": updated.status, "clinical_stage": updated.clinical_stage}
