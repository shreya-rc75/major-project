from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class ReportReview(Base):
    __tablename__ = "report_reviews"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="pending")  # pending, approved, rejected
    comment = Column(Text, nullable=True)
    stage_review = Column(String(64), nullable=True)
    risk_review = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now(), onupdate=func.now())

    report = relationship("Report", backref="reviews")

    def __repr__(self):
        return f"<ReportReview id={self.id} report_id={self.report_id} status={self.status}>"
