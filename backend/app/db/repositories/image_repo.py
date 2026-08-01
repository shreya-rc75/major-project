from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.image import Image


def get_image(db: Session, image_id: int) -> Optional[Image]:
    return db.query(Image).filter(Image.id == image_id).one_or_none()


def list_images_by_study(db: Session, study_id: int, skip: int = 0, limit: int = 50) -> List[Image]:
    return db.query(Image).filter(Image.study_id == study_id).order_by(Image.uploaded_at.desc()).offset(skip).limit(limit).all()


def create_image(db: Session, image_in: dict) -> Image:
    image = Image(**image_in)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def update_image(db: Session, image: Image, updates: dict) -> Image:
    for k, v in updates.items():
        setattr(image, k, v)
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def delete_image(db: Session, image: Image) -> None:
    db.delete(image)
    db.commit()
