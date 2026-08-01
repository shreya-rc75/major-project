from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.base import Base


class Study(Base):
    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    accession = Column(String(128), nullable=False, unique=True, index=True)
    clinician = Column(String(255), nullable=True)
    study_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    patient = relationship("Patient", back_populates="studies")
    images = relationship("Image", back_populates="study", cascade="all, delete-orphan")
    analyses = relationship("AnalysisResult", back_populates="study", cascade="all, delete-orphan")
    visualizations = relationship("Visualization", back_populates="study", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Study id={self.id} accession={self.accession} patient_id={self.patient_id}>"
