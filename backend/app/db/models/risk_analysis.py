from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, JSON, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class RiskAnalysis(Base):
    __tablename__ = "risk_analysis"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False, index=True)
    risk_1y = Column(Float, nullable=True)
    risk_3y = Column(Float, nullable=True)
    risk_5y = Column(Float, nullable=True)
    risk_category = Column(String(32), nullable=True)
    confidence = Column(Float, nullable=True)
    recommendations = Column(JSON, nullable=True)
    contributing_factors = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    analysis = relationship("AnalysisResult", backref="risk_analysis")

    def __repr__(self):
        return f"<RiskAnalysis id={self.id} analysis_id={self.analysis_id} category={self.risk_category}>"
