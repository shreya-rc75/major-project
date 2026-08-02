from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/patients", tags=["patients"])

@router.post("/", response_model=schemas.PatientOut, status_code=status.HTTP_201_CREATED)
def create_patient(patient_in: schemas.PatientCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    patient = models.Patient(**patient_in.dict())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@router.get("/", response_model=List[schemas.PatientOut])
def list_patients(q: str = None, skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    query = db.query(models.Patient)
    if q:
        qlike = f"%{q}%"
        query = query.filter(models.Patient.name.ilike(qlike))
    patients = query.offset(skip).limit(limit).all()
    return patients

@router.get("/{patient_id}", response_model=schemas.PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.put("/{patient_id}", response_model=schemas.PatientOut)
def update_patient(patient_id: int, patient_in: schemas.PatientCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for k, v in patient_in.dict().items():
        setattr(patient, k, v)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient

@router.delete("/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_patient(patient_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"ok": True}
