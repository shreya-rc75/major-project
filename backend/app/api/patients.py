"""Patient management endpoints."""
import logging
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from app import models, schemas
from app.database import get_db
from app.api.auth import get_current_user
from app.core.exceptions import ResourceNotFoundException, ValidationException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post(
    "/",
    response_model=schemas.PatientOut,
    status_code=status.HTTP_201_CREATED
)
def create_patient(
    patient_in: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create a new patient record.
    
    Requires authentication.
    """
    try:
        patient = models.Patient(**patient_in.dict())
        db.add(patient)
        db.commit()
        db.refresh(patient)
        logger.info(f"Patient created: {patient.id} by {current_user.email}")
        return patient
    except Exception as e:
        logger.error(f"Failed to create patient: {e}")
        db.rollback()
        raise ValidationException(detail="Failed to create patient")


@router.get("/", response_model=List[schemas.PatientOut])
def list_patients(
    q: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List patients with optional search.
    
    Requires authentication.
    
    Args:
        q: Search query (searches patient name)
        skip: Number of records to skip (pagination)
        limit: Number of records to return (max 50)
    
    Returns:
        List of patient records
    """
    try:
        query = db.query(models.Patient)
        
        if q:
            query = query.filter(models.Patient.name.ilike(f"%{q}%"))
        
        patients = query.offset(skip).limit(limit).all()
        return patients
    except Exception as e:
        logger.error(f"Failed to list patients: {e}")
        raise ValidationException(detail="Failed to retrieve patients")


@router.get("/{patient_id}", response_model=schemas.PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Get a specific patient by ID.
    
    Requires authentication.
    """
    try:
        patient = db.query(models.Patient).filter(
            models.Patient.id == patient_id
        ).first()
        
        if not patient:
            raise ResourceNotFoundException("Patient", str(patient_id))
        
        return patient
    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to get patient {patient_id}: {e}")
        raise ValidationException(detail="Failed to retrieve patient")


@router.put("/{patient_id}", response_model=schemas.PatientOut)
def update_patient(
    patient_id: int,
    patient_in: schemas.PatientCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update a patient record.
    
    Requires authentication.
    """
    try:
        patient = db.query(models.Patient).filter(
            models.Patient.id == patient_id
        ).first()
        
        if not patient:
            raise ResourceNotFoundException("Patient", str(patient_id))
        
        for key, value in patient_in.dict().items():
            setattr(patient, key, value)
        
        db.add(patient)
        db.commit()
        db.refresh(patient)
        logger.info(f"Patient updated: {patient_id} by {current_user.email}")
        return patient
    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to update patient {patient_id}: {e}")
        db.rollback()
        raise ValidationException(detail="Failed to update patient")


@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a patient record.
    
    Requires authentication.
    """
    try:
        patient = db.query(models.Patient).filter(
            models.Patient.id == patient_id
        ).first()
        
        if not patient:
            raise ResourceNotFoundException("Patient", str(patient_id))
        
        db.delete(patient)
        db.commit()
        logger.info(f"Patient deleted: {patient_id} by {current_user.email}")
        return None
    except ResourceNotFoundException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete patient {patient_id}: {e}")
        db.rollback()
        raise ValidationException(detail="Failed to delete patient")
