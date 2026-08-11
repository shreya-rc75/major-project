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
    role = Column(String(64), nullable=True, default="Pathologist")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("Case", back_populates="created_by_user")
    reports = relationship("Report", back_populates="uploaded_by")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    patient_identifier = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(256), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(32), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(256), nullable=True)
    address = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    cases = relationship("Case", back_populates="patient")
    reports = relationship("Report", back_populates="patient")

class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    clinical_data = Column(Text, nullable=True)
    status = Column(String(50), default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="cases")
    created_by_user = relationship("User", back_populates="cases")
    images = relationship("Image", back_populates="case")
    predictions = relationship("Prediction", back_populates="case")
    reports = relationship("Report", back_populates="case")

class Image(Base):
    __tablename__ = "images"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    filename = Column(String(512), nullable=False)
    filepath = Column(String(1024), nullable=False)
    file_type = Column(String(128), nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="images")

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String(64), nullable=True)
    predicted_stage = Column(String(128), nullable=True)
    confidence = Column(Float, nullable=True)
    model_version = Column(String(64), nullable=True)
    prediction_details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="predictions")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    report_text = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="reports")
    patient = relationship("Patient", back_populates="reports")
    uploaded_by = relationship("User", back_populates="reports")
