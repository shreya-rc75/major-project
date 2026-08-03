from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Visualization(Base):
    __tablename__ = "visualizations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False, index=True)
    mesh_path = Column(String(1024), nullable=False)
    texture_path = Column(String(1024), nullable=True)
    metadata = Column(Text, nullable=True)  # JSON string
    volume = Column(Float, nullable=True)
    surface_area = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    analysis = relationship("AnalysisResult", backref="visualizations")

    def __repr__(self):
        return f"<Visualization id={self.id} analysis_id={self.analysis_id}>"
