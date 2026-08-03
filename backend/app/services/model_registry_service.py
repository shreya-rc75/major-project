from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.db.repositories.model_registry_repo import (
    create_model as repo_create,
    get_model as repo_get,
    list_models as repo_list,
    set_active_model as repo_set_active,
    get_active_model as repo_get_active,
    update_model as repo_update,
    delete_model as repo_delete,
)
import logging

logger = logging.getLogger(__name__)


class ModelRegistryService:
    """Service to manage model registry entries and active model loading.

    The service maintains an in-memory cached active model to avoid re-loading
    weights on every inference call. The load_active_model method attempts to
    instantiate the model object using the AI model loader if available.
    """

    def __init__(self, db: Session):
        self.db = db
        self._loaded_model = None
        self._loaded_model_id = None

    def register_model(self, model_in: Dict[str, Any]):
        m = repo_create(self.db, model_in)
        logger.info("Registered model %s:%s id=%s", m.model_name, m.version, m.id)
        return m

    def list_models(self, limit: int = 50, offset: int = 0):
        return repo_list(self.db, limit=limit, offset=offset)

    def get_model(self, model_id: int) -> Optional[Any]:
        return repo_get(self.db, model_id)

    def set_active(self, model_id: int):
        m = repo_set_active(self.db, model_id)
        # invalidate cache
        self._loaded_model = None
        self._loaded_model_id = None
        logger.info("Set active model id=%s", m.id)
        return m

    def get_active(self):
        return repo_get_active(self.db)

    def load_active_model(self):
        """
        Load and return the active model object. If no model is active, returns None.
        This method will attempt to use the project's AI model loader if present;
        otherwise it will return the weights_path string as a placeholder.
        """
        active = self.get_active()
        if not active:
            logger.warning("No active model configured in registry")
            return None
        if self._loaded_model_id == active.id and self._loaded_model is not None:
            return self._loaded_model

        # Try to load using standard model loader if available
        try:
            # Attempt import path for model loader
            from app.ai.model.model import load_model_from_weights
            logger.info("Loading model weights from %s", active.weights_path)
            m = load_model_from_weights(active.weights_path)
            self._loaded_model = m
            self._loaded_model_id = active.id
            logger.info("Active model loaded: %s (id=%s)", active.model_name, active.id)
            return m
        except Exception as exc:
            logger.exception("Model loader not available or failed to load weights: %s", exc)
            # Fallback: keep weights_path as placeholder
            self._loaded_model = active.weights_path
            self._loaded_model_id = active.id
            return self._loaded_model

    def update_model(self, model_id: int, updates: Dict[str, Any]):
        m = repo_get(self.db, model_id)
        if not m:
            raise RuntimeError("Model not found")
        return repo_update(self.db, m, updates)

    def delete_model(self, model_id: int):
        m = repo_get(self.db, model_id)
        if not m:
            raise RuntimeError("Model not found")
        repo_delete(self.db, m)
        logger.info("Deleted model id=%s", model_id)
        return True
