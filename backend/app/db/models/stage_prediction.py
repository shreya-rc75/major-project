from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class StagePrediction(Base):
    __tablename__ = "stage_predictions"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=True)
    explanation = Column(Text, nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    analysis = relationship("AnalysisResult", backref="stage_predictions")

    def __repr__(self):
        return f"<StagePrediction id={self.id} analysis_id={self.analysis_id} stage={self.stage}>" 
