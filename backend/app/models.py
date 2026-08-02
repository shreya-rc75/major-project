from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(256), unique=True, index=True, nullable=False)
    hashed_password = Column(String(256), nullable=False)
    full_name = Column(String(256), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="uploaded_by")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(256), nullable=False)
    age = Column(Integer, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(256), nullable=True)
    address = Column(Text, nullable=True)
    blood_group = Column(String(10), nullable=True)
    previous_diagnosis = Column(Text, nullable=True)
    smoking = Column(Boolean, default=False)
    hpv_status = Column(String(50), nullable=True)
    family_history = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="patient")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String(1024), nullable=False)
    prediction = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    probabilities = Column(Text, nullable=True)  # store JSON string
    gradcam_path = Column(String(1024), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="reports")
    uploaded_by = relationship("User", back_populates="reports")
