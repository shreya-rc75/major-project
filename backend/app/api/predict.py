"""AI model prediction endpoints."""
import os
import uuid
import json
import logging
from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.api.auth import get_current_user
from app.core.exceptions import (
    ResourceNotFoundException,
    ValidationException,
    InternalServerException,
)
from app.core.config import settings

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
            prediction_service = PredictService(
                model_path=settings.MODEL_PATH
            )
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
    
    Args:
        patient_id: ID of patient for this assessment
        file: Image file to analyze
        db: Database session
        current_user: Authenticated user
    
    Returns:
        Prediction result with confidence and probabilities
    
    Raises:
        ResourceNotFoundException: If patient not found
        ValidationException: If file validation fails
        InternalServerException: If model is unavailable
    """
    global prediction_service, model_available
    
    try:
        # Validate patient exists
        patient = db.query(models.Patient).filter(
            models.Patient.id == patient_id
        ).first()
        
        if not patient:
            raise ResourceNotFoundException("Patient", str(patient_id))
        
        # Check if model is available
        if not model_available:
            if prediction_service is None:
                init_prediction_service()
            
            if not model_available:
                raise InternalServerException(
                    detail="AI model is not available. Please try again later."
                )
        
        # Validate file
        if not file.filename:
            raise ValidationException(detail="No filename provided")
        
        allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp"}
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise ValidationException(
                detail=f"File type not supported. Allowed: {allowed_extensions}"
            )
        
        # Save uploaded file
        fname = f"{uuid.uuid4().hex}{file_ext}"
        fpath = os.path.join(settings.UPLOAD_DIR, fname)
        
        with open(fpath, "wb") as fh:
            fh.write(file.file.read())
        
        logger.info(f"File uploaded: {fname} for patient {patient_id}")
        
        # Run prediction
        result = prediction_service.predict(fpath)
        
        # Store report in database
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
        raise InternalServerException(
            detail="Failed to process image prediction"
        )


@router.get("/health", tags=["system"])
def prediction_health():
    """Check if AI prediction service is available."""
    global model_available
    
    if prediction_service is None:
        init_prediction_service()
    
    return {
        "model_available": model_available,
        "model_path": settings.MODEL_PATH if model_available else None,
        "status": "ready" if model_available else "unavailable"
    }
