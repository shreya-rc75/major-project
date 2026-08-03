from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.visualization_repo import get_visualization
from app.services.visualization_service import VisualizationService
from app.services.storage_service import LocalFileStorage
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/visualization", tags=["visualization"])

# auth placeholder
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


@router.post("/generate/{analysis_id}")
def generate_visualization(analysis_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = VisualizationService()
    res = svc.generate_visualization(db, analysis_id)
    if not res:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Visualization generation failed")
    return res


@router.get("/{vis_id}")
def get_visualization(vis_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    v = get_visualization(db, vis_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found")
    # return metadata and urls
    storage = LocalFileStorage()
    mesh_url = None
    mask_url = None
    try:
        mesh_url = storage.url_for(v.mesh_path) if v.mesh_path else None
    except Exception:
        logger.exception("Failed to get mesh URL for %s", v.mesh_path)
    try:
        mask_url = storage.url_for(v.metadata) if v.metadata else None
    except Exception:
        # metadata wasn't a path; ignore
        mask_url = None
    return {"id": v.id, "analysis_id": v.analysis_id, "mesh_url": mesh_url, "metadata": v.metadata, "volume": v.volume, "surface_area": v.surface_area}


@router.get("/download/{vis_id}")
def download_visualization(vis_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    v = get_visualization(db, vis_id)
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visualization not found")
    storage = LocalFileStorage()
    try:
        file_bytes = storage.read_file(v.mesh_path)
    except Exception as exc:
        logger.exception("Failed to read mesh file %s: %s", v.mesh_path, exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to read mesh file")
    return Response(content=file_bytes, media_type="model/gltf-binary", headers={"Content-Disposition": f"attachment; filename=visualization_{vis_id}.glb"})
