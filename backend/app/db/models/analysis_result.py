from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id = Column(Integer, ForeignKey("images.id", ondelete="SET NULL"), nullable=True, index=True)
    model_name = Column(String(255), nullable=False)
    model_version = Column(String(64), nullable=True)
    predicted_class = Column(String(128), nullable=True)
    probabilities = Column(JSON, nullable=True)
    clinical_stage = Column(String(64), nullable=True)
    risk_score = Column(Float, nullable=True)
    gradcam_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    status = Column(String(50), nullable=False, default="pending")

    study = relationship("Study", back_populates="analyses")
    image = relationship("Image", back_populates="analyses")

    def __repr__(self):
        return f"<AnalysisResult id={self.id} study_id={self.study_id} status={self.status}>"
