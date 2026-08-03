"""Modify inference entrypoint to automatically load active model from registry before running inference."""
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

try:
    # existing inference implementation (kept if present)
    from app.ai.inference._impl import run_inference_impl
except Exception:
    run_inference_impl = None


def run_inference(input_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run model inference using the currently active model from the registry.

    This function will attempt to load the active model via ModelRegistryService
    (which may return a model object or a weights_path placeholder). If a
    concrete runnable model object is available and provides a `predict` API,
    it will be used. Otherwise, fall back to the project's existing inference
    implementation if present.
    """
    try:
        # Lazy import to avoid circular dependencies at module import time
        from app.db.session import SessionLocal
        from app.services.model_registry_service import ModelRegistryService

        db = SessionLocal()
        mgr = ModelRegistryService(db)
        model_obj = mgr.load_active_model()
        db.close()

        # If model_obj is a string (weights path) or None, fall back
        if model_obj is None or isinstance(model_obj, str):
            logger.info("No runnable active model found; falling back to default inference implementation")
            if run_inference_impl:
                return run_inference_impl(input_payload)
            else:
                raise RuntimeError("No inference implementation available and no active model loaded")

        # If model_obj exposes a `predict` method use it
        if hasattr(model_obj, "predict"):
            preds = model_obj.predict(input_payload)
            return preds

        # fallback
        if run_inference_impl:
            return run_inference_impl(input_payload)

        raise RuntimeError("Active model loaded but does not expose a predict method")
    except Exception as exc:
        logger.exception("Inference failed to run: %s", exc)
        raise
