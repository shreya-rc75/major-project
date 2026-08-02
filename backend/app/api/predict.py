import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from ..database import get_db
from .. import models, schemas
from .auth import get_current_user
from ..ai.predict import PredictService

router = APIRouter(prefix="/predict", tags=["predict"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Initialize predict service (loads model)
predict_service = PredictService(model_path=os.getenv("MODEL_PATH", "./models/efficientnet_b3_best.pth"))

@router.post("/", response_model=schemas.PredictionOut)
def predict_image(patient_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Validate patient
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Save file to disk
    file_ext = os.path.splitext(file.filename)[1] or ".jpg"
    fname = f"{uuid.uuid4().hex}{file_ext}"
    fpath = os.path.join(UPLOAD_DIR, fname)
    with open(fpath, "wb") as fh:
        fh.write(file.file.read())

    try:
        result = predict_service.predict(fpath)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Persist report
    import json
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

    return schemas.PredictionOut(
        prediction=result["prediction"],
        confidence=float(result["confidence"]),
        probabilities=result.get("probabilities", {}),
        gradcam_url=result.get("gradcam_path")
    )
