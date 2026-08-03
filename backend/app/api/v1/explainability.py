from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.analysis_repo import get_analysis
from app.ai.explainability.explain import ExplainabilityService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/analysis", tags=["explainability"])

# auth placeholder
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


@router.get("/{analysis_id}/gradcam")
def get_gradcam(analysis_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    svc = ExplainabilityService()
    # assume gradcam path stored in analysis.gradcam_path
    gradcam_rel = getattr(analysis, "gradcam_path", None)
    if gradcam_rel:
        try:
            url = svc.storage.url_for(gradcam_rel)
            return {"gradcam_url": url}
        except Exception:
            logger.exception("Failed to generate gradcam URL for analysis %s", analysis_id)
            raise HTTPException(status_code=500, detail="Failed to fetch Grad-CAM")
    # fallback: try to generate artifacts
    out = svc.generate_all(analysis_id)
    urls = svc.get_urls(out)
    return {"gradcam_url": urls.get("gradcam")}


@router.get("/{analysis_id}/saliency")
def get_saliency(analysis_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    svc = ExplainabilityService()
    rel = svc.generate_saliency_map(analysis_id)
    if not rel:
        raise HTTPException(status_code=500, detail="Failed to generate saliency map")
    try:
        url = svc.storage.url_for(rel)
        return {"saliency_url": url}
    except Exception:
        logger.exception("Failed to get saliency URL for %s", analysis_id)
        raise HTTPException(status_code=500, detail="Failed to fetch saliency image")


@router.get("/{analysis_id}/explanation")
def get_explanation(analysis_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
    svc = ExplainabilityService()
    rel = svc.generate_explanation_json(analysis_id)
    if not rel:
        raise HTTPException(status_code=500, detail="Failed to generate explanation")
    try:
        url = svc.storage.url_for(rel)
        return {"explanation_url": url}
    except Exception:
        logger.exception("Failed to get explanation URL for %s", analysis_id)
        raise HTTPException(status_code=500, detail="Failed to fetch explanation JSON")
