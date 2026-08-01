from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.patient import Patient


def get_patient(db: Session, patient_id: int) -> Optional[Patient]:
    return db.query(Patient).filter(Patient.id == patient_id).one_or_none()


def get_patient_by_identifier(db: Session, identifier: str) -> Optional[Patient]:
    return db.query(Patient).filter(Patient.patient_identifier == identifier).one_or_none()


def list_patients(db: Session, skip: int = 0, limit: int = 50) -> List[Patient]:
    return db.query(Patient).order_by(Patient.created_at.desc()).offset(skip).limit(limit).all()


def create_patient(db: Session, *, patient_in: dict) -> Patient:
    patient = Patient(**patient_in)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient: Patient, updates: dict) -> Patient:
    for k, v in updates.items():
        setattr(patient, k, v)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient: Patient) -> None:
    db.delete(patient)
    db.commit()
