from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.db.models.model_registry import ModelRegistry
from sqlalchemy import desc


def create_model(db: Session, model_in: Dict[str, Any]) -> ModelRegistry:
    m = ModelRegistry(
        model_name=model_in["model_name"],
        version=model_in["version"],
        framework=model_in.get("framework"),
        accuracy=model_in.get("accuracy"),
        precision=model_in.get("precision"),
        recall=model_in.get("recall"),
        f1_score=model_in.get("f1_score"),
        weights_path=model_in["weights_path"],
        active=model_in.get("active", False),
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def get_model(db: Session, model_id: int) -> Optional[ModelRegistry]:
    return db.query(ModelRegistry).filter(ModelRegistry.id == model_id).one_or_none()


def list_models(db: Session, limit: int = 50, offset: int = 0) -> List[ModelRegistry]:
    return db.query(ModelRegistry).order_by(desc(ModelRegistry.created_at)).limit(limit).offset(offset).all()


def get_active_model(db: Session) -> Optional[ModelRegistry]:
    return db.query(ModelRegistry).filter(ModelRegistry.active == True).order_by(desc(ModelRegistry.created_at)).first()


def set_active_model(db: Session, model_id: int) -> ModelRegistry:
    # Deactivate all models and activate the requested one within a transaction
    m = db.query(ModelRegistry).filter(ModelRegistry.id == model_id).one_or_none()
    if not m:
        raise ValueError("Model not found")
    # deactivate others
    db.query(ModelRegistry).filter(ModelRegistry.active == True).update({"active": False})
    m.active = True
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def update_model(db: Session, model: ModelRegistry, updates: Dict[str, Any]) -> ModelRegistry:
    for k, v in updates.items():
        setattr(model, k, v)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model: ModelRegistry) -> None:
    db.delete(model)
    db.commit()
