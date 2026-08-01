from sqlalchemy import Column, Integer, String, Date, DateTime, Text, func, Enum
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_identifier = Column(String(128), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(Enum(GenderEnum), nullable=True)
    contact = Column(String(128), nullable=True)
    medical_record = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=False), nullable=False, server_default=func.now())

    studies = relationship("Study", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Patient id={self.id} identifier={self.patient_identifier} name={self.full_name}>"
