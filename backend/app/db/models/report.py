from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, nullable=False, index=True)
    analysis_id = Column(Integer, ForeignKey("analysis_results.id", ondelete="CASCADE"), nullable=False, index=True)
    pdf_path = Column(String(1024), nullable=False)
    html_path = Column(String(1024), nullable=True)
    report_status = Column(String(32), nullable=False, default="created")
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now())

    analysis = relationship("AnalysisResult", backref="reports")

    def __repr__(self):
        return f"<Report id={self.id} analysis_id={self.analysis_id} status={self.report_status}>"
