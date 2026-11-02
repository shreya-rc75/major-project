"""AI model prediction endpoints."""
import json
import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.ai.preprocessing import ALLOWED_IMAGE_EXTENSIONS, validate_image_upload
from app.api.auth import get_current_user
from app.core.config import settings
from app.core.exceptions import (
    InternalServerException,
    ResourceNotFoundException,
    ValidationException,
)
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["predict"])

# Initialize prediction service (lazy loading to avoid crash at startup)
prediction_service = None
model_available = False


def init_prediction_service():
    """Initialize the AI prediction service (lazy loading)."""
    global prediction_service, model_available

    try:
        from app.ai.predict import PredictService

        if os.path.exists(settings.MODEL_PATH):
            prediction_service = PredictService(model_path=settings.MODEL_PATH)
            model_available = True
            logger.info(f"AI model loaded from {settings.MODEL_PATH}")
        else:
            logger.warning(
                f"AI model not found at {settings.MODEL_PATH}. "
                "Predictions will not be available."
            )
            model_available = False
    except Exception as e:
        logger.error(f"Failed to initialize prediction service: {e}")
        model_available = False


@router.post("/", response_model=schemas.PredictionOut)
def predict_image(
    patient_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Upload image and get AI prediction.

    Requires authentication.
    """
    global prediction_service, model_available

    try:
        patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
        if not patient:
            raise ResourceNotFoundException("Patient", str(patient_id))

        if not model_available:
            if prediction_service is None:
                init_prediction_service()
            if not model_available:
                raise InternalServerException(detail="AI model is not available. Please try again later.")

        if not file.filename:
            raise ValidationException(detail="No filename provided")

        contents = file.file.read()
        validate_image_upload(file.filename, len(contents), ALLOWED_IMAGE_EXTENSIONS)

        file_ext = os.path.splitext(file.filename)[1].lower()
        fname = f"{uuid.uuid4().hex}{file_ext}"
        fpath = os.path.join(settings.UPLOAD_DIR, fname)

        with open(fpath, "wb") as fh:
            fh.write(contents)

        logger.info(f"File uploaded: {fname} for patient {patient_id}")

        result = prediction_service.predict(fpath)

        report = models.Report(
            patient_id=patient.id,
            uploaded_by_id=current_user.id,
            image_path=fpath,
            prediction=result["prediction"],
            confidence=float(result["confidence"]),
            probabilities=json.dumps(result.get("probabilities", {})),
            gradcam_path=result.get("gradcam_path"),
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        logger.info(
            f"Prediction created: {result['prediction']} "
            f"({result['confidence']:.2%} confidence) for patient {patient_id}"
        )

        return schemas.PredictionOut(
            prediction=result["prediction"],
            confidence=float(result["confidence"]),
            probabilities=result.get("probabilities", {}),
            gradcam_url=result.get("gradcam_path"),
        )

    except (ResourceNotFoundException, ValidationException, InternalServerException):
        raise
    except Exception as e:
        logger.error(f"Prediction error for patient {patient_id}: {e}")
        db.rollback()
        raise InternalServerException(detail="Failed to process image prediction")


@router.get("/health", tags=["system"])
def prediction_health():
    """Check if AI prediction service is available."""
    global model_available

    if prediction_service is None:
        init_prediction_service()

    return {
        "model_available": model_available,
        "model_path": settings.MODEL_PATH if model_available else None,
        "status": "ready" if model_available else "unavailable",
    }
