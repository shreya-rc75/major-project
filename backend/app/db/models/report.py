from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id", ondelete="CASCADE"), nullable=False, index=True)
    report_path = Column(String(1024), nullable=True)
    pdf_path = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    study = relationship("Study", back_populates="reports")

    def __repr__(self):
        return f"<Report id={self.id} study_id={self.study_id}>"
