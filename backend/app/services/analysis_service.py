from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.repositories.analysis_repo import get_analysis, update_analysis, update_analysis_no_commit
from app.db.repositories.stage_prediction_repo import create_stage_prediction, create_stage_prediction_no_commit
from app.db.repositories.risk_repo import create_risk_analysis, create_risk_analysis_no_commit
from fastapi import HTTPException, status
from app.ai.clinical.stage_estimator import estimate_stage
from app.ai.risk.risk_model import predict_risk


def run_analysis_and_persist(db: Session, analysis_id: int, model_inference_result: Dict[str, Any], clinical_data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Persist inference outputs into AnalysisResult and return the updated record.
    This function now:
      - computes stage_estimation and risk_prediction (explainable heuristics)
      - attempts to persist AnalysisResult, StagePrediction, and RiskAnalysis in a single transaction
      - if risk persistence causes a DB error, rolls back and persists AnalysisResult+StagePrediction (without risk)
      - if anything else fails during persistence, marks the analysis as failed and raises

    model_inference_result expected keys: predicted_class, probabilities (dict), gradcam_bytes (optional), risk_score (optional), per_cell_features (optional)
    clinical_data: optional dict containing clinical inputs (hpv, biopsy, imaging, symptoms)
    """
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    # Prepare analysis updates from model outputs
    updates = {
        "predicted_class": model_inference_result.get("predicted_class"),
        "probabilities": model_inference_result.get("probabilities"),
        "risk_score": model_inference_result.get("risk_score"),
        "status": "completed",
    }

    # Compute stage and risk using pure functions (so errors here don't touch DB)
    try:
        stage_result = estimate_stage(clinical_data, model_inference_result.get("probabilities", {}), model_inference_result.get("per_cell_features"))
    except Exception:
        stage_result = None

    try:
        risk_result = predict_risk(clinical_data, model_inference_result.get("probabilities", {}), model_inference_result.get("per_cell_features"))
    except Exception:
        risk_result = None

    # Handle gradcam bytes (save to storage) before DB transaction so storage errors are caught separately
    gradcam_bytes = model_inference_result.get("gradcam_bytes")
    if gradcam_bytes:
        from app.services.storage_service import LocalFileStorage
        from uuid import uuid4
        storage = LocalFileStorage()
        rel_path, size = storage.save_file(gradcam_bytes, filename=f"gradcam_{uuid4().hex}.png", subpath=f"studies/{analysis.study_id}/analysis")
        updates["gradcam_path"] = rel_path

    # Now attempt to persist everything in a single transaction
    try:
        with db.begin():
            # update analysis without committing in repo (no commit inside)
            update_analysis_no_commit(db, analysis=analysis, updates=updates)

            # persist stage prediction (no commit)
            if stage_result:
                create_stage_prediction_no_commit(db, stage_in={
                    "analysis_id": analysis_id,
                    "stage": stage_result.get("stage"),
                    "confidence": stage_result.get("confidence"),
                    "explanation": stage_result.get("explanation"),
                    "contributing_factors": stage_result.get("contributing_factors"),
                })

            # persist risk prediction (no commit)
            if risk_result:
                create_risk_analysis_no_commit(db, risk_in={
                    "analysis_id": analysis_id,
                    "risk_1y": risk_result.get("risk_1y"),
                    "risk_3y": risk_result.get("risk_3y"),
                    "risk_5y": risk_result.get("risk_5y"),
                    "risk_category": risk_result.get("risk_category"),
                    "confidence": risk_result.get("confidence"),
                    "recommendations": risk_result.get("recommendations"),
                    "contributing_factors": risk_result.get("contributing_factors"),
                })
        # If we reach here the transaction committed successfully
    except Exception as db_exc:
        # Rollback has already been done by context manager. Try to persist analysis + stage (without risk) as best-effort.
        try:
            db.rollback()
        except Exception:
            pass
        try:
            with db.begin():
                # update analysis
                update_analysis_no_commit(db, analysis=analysis, updates=updates)
                # persist stage only
                if stage_result:
                    create_stage_prediction_no_commit(db, stage_in={
                        "analysis_id": analysis_id,
                        "stage": stage_result.get("stage"),
                        "confidence": stage_result.get("confidence"),
                        "explanation": stage_result.get("explanation"),
                        "contributing_factors": stage_result.get("contributing_factors"),
                    })
        except Exception as final_exc:
            # If even this fails, mark analysis as failed and re-raise
            try:
                update_analysis(db, analysis=analysis, updates={"status": "failed"})
            except Exception:
                pass
            raise final_exc

    # Return summary
    result = {"analysis_id": analysis_id, "status": "completed", "clinical_stage": (stage_result.get("stage") if stage_result else None)}
    if risk_result:
        result["risk"] = risk_result
    return result
