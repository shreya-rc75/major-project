from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    mesh_path = Column(String(1024), nullable=True)
    texture_path = Column(String(1024), nullable=True)
    metadata = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    status = Column(String(50), nullable=False, default="pending")

    study = relationship("Study", back_populates="visualizations")

    def __repr__(self):
        return f"<Visualization id={self.id} study_id={self.study_id} status={self.status}>"
