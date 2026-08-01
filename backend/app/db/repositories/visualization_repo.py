from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models.visualization import Visualization


def get_visualization(db: Session, viz_id: int) -> Optional[Visualization]:
    return db.query(Visualization).filter(Visualization.id == viz_id).one_or_none()


def list_visualizations_by_study(db: Session, study_id: int, skip: int = 0, limit: int = 50) -> List[Visualization]:
    return db.query(Visualization).filter(Visualization.study_id == study_id).order_by(Visualization.created_at.desc()).offset(skip).limit(limit).all()


def create_visualization(db: Session, viz_in: dict) -> Visualization:
    viz = Visualization(**viz_in)
    db.add(viz)
    db.commit()
    db.refresh(viz)
    return viz


def update_visualization(db: Session, viz: Visualization, updates: dict) -> Visualization:
    for k, v in updates.items():
        setattr(viz, k, v)
    db.add(viz)
    db.commit()
    db.refresh(viz)
    return viz


def delete_visualization(db: Session, viz: Visualization) -> None:
    db.delete(viz)
    db.commit()
