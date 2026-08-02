from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db.repositories.analysis_repo import get_analysis, update_analysis
from fastapi import HTTPException, status
from app.ai.clinical.stage_estimator import estimate_stage


def run_analysis_and_persist(db: Session, analysis_id: int, model_inference_result: Dict[str, Any], clinical_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Persist inference outputs into AnalysisResult and return the updated record.
    model_inference_result expected keys: predicted_class, probabilities (dict), gradcam_bytes (optional), risk_score (optional)
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

    # Compute clinical stage using estimator
    try:
        stage_result = estimate_stage(clinical_data, model_inference_result.get("probabilities", {}), model_inference_result.get("per_cell_features"))
        updates["clinical_stage"] = stage_result.get("stage")
        # Add stage metadata into probabilities field under a key for traceability
        probs = updates.get("probabilities") or {}
        probs = dict(probs)
        probs["_stage_estimator"] = {
            "stage": stage_result.get("stage"),
            "confidence": stage_result.get("confidence"),
            "explanation": stage_result.get("explanation"),
            "contributing_factors": stage_result.get("contributing_factors"),
            "normalized_score": stage_result.get("normalized_score"),
        }
        updates["probabilities"] = probs
    except Exception as exc:
        # If stage estimation fails, log minimal info and continue to persist model outputs
        # We do not stop the whole pipeline for stage estimator failure
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
