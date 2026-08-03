from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.model_registry_service import ModelRegistryService
from app.schemas.model_registry_schemas import ModelCreate, ModelOut
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/models", tags=["models"])

# auth placeholder
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


@router.post("/", response_model=ModelOut)
def register_model(payload: ModelCreate, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ModelRegistryService(db)
    try:
        m = svc.register_model(payload.dict())
        # if active flag set, set active
        if payload.active:
            svc.set_active(m.id)
        return m
    except Exception as exc:
        logger.exception("Failed to register model: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/", response_model=List[ModelOut])
def list_models(db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ModelRegistryService(db)
    return svc.list_models()


@router.get("/active", response_model=ModelOut)
def get_active(db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ModelRegistryService(db)
    m = svc.get_active()
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active model not found")
    return m


@router.post("/activate/{model_id}", response_model=ModelOut)
def activate_model(model_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ModelRegistryService(db)
    try:
        m = svc.set_active(model_id)
        return m
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    except Exception as exc:
        logger.exception("Failed to activate model: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/{model_id}", response_model=ModelOut)
def get_model(model_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ModelRegistryService(db)
    m = svc.get_model(model_id)
    if not m:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")
    return m


@router.put("/{model_id}", response_model=ModelOut)
def update_model(model_id: int, payload: ModelCreate, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ModelRegistryService(db)
    try:
        m = svc.update_model(model_id, payload.dict())
        return m
    except Exception as exc:
        logger.exception("Failed to update model: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = ModelRegistryService(db)
    try:
        svc.delete_model(model_id)
        return {"success": True}
    except Exception as exc:
        logger.exception("Failed to delete model: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
