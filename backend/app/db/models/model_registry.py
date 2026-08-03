from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, func
from app.db.base import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(256), nullable=False)
    version = Column(String(64), nullable=False)
    framework = Column(String(64), nullable=True)
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    weights_path = Column(String(1024), nullable=False)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    active = Column(Boolean, nullable=False, default=False)

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<ModelRegistry id={self.id} name={self.model_name} v={self.version} active={self.active}>"
