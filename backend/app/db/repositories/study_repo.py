from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.study import Study


def get_study(db: Session, study_id: int) -> Optional[Study]:
    return db.query(Study).filter(Study.id == study_id).one_or_none()


def get_study_by_accession(db: Session, accession: str) -> Optional[Study]:
    return db.query(Study).filter(Study.accession == accession).one_or_none()


def list_studies_by_patient(db: Session, patient_id: int, skip: int = 0, limit: int = 50) -> List[Study]:
    return (db.query(Study).filter(Study.patient_id == patient_id).order_by(Study.created_at.desc()).offset(skip).limit(limit).all())


def create_study(db: Session, study_in: dict) -> Study:
    study = Study(**study_in)
    db.add(study)
    db.commit()
    db.refresh(study)
    return study


def update_study(db: Session, study: Study, updates: dict) -> Study:
    for k, v in updates.items():
        setattr(study, k, v)
    db.add(study)
    db.commit()
    db.refresh(study)
    return study


def delete_study(db: Session, study: Study) -> None:
    db.delete(study)
    db.commit()
