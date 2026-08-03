from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models.visualization import Visualization


def create_visualization(db: Session, vis_in: Dict[str, Any]) -> Visualization:
    v = Visualization(
        analysis_id=vis_in["analysis_id"],
        mesh_path=vis_in["mesh_path"],
        texture_path=vis_in.get("texture_path"),
        metadata=vis_in.get("metadata"),
        volume=vis_in.get("volume"),
        surface_area=vis_in.get("surface_area"),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return v


def get_visualization(db: Session, vis_id: int) -> Optional[Visualization]:
    return db.query(Visualization).filter(Visualization.id == vis_id).one_or_none()


def list_visualizations(db: Session, limit: int = 50, offset: int = 0) -> List[Visualization]:
    return db.query(Visualization).order_by(Visualization.created_at.desc()).limit(limit).offset(offset).all()


def delete_visualization(db: Session, vis: Visualization) -> None:
    db.delete(vis)
    db.commit()
