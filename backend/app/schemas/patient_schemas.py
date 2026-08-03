from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class PatientProfile(BaseModel):
    id: int
    patient_identifier: Optional[str]
    full_name: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class AnalysisHistoryEntry(BaseModel):
    analysis_id: int
    analysis_date: Optional[datetime]
    status: Optional[str]
    predicted_class: Optional[str]
    probabilities: Optional[Dict[str, float]]
    study_id: Optional[int]
    accession: Optional[str]
    image_id: Optional[int]
    filename: Optional[str]


class ReportEntry(BaseModel):
    id: int
    analysis_id: int
    pdf_path: str
    html_path: Optional[str]
    status: str
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class RiskEntry(BaseModel):
    analysis_id: int
    created_at: Optional[datetime]
    risk_1y: Optional[float]
    risk_3y: Optional[float]
    risk_5y: Optional[float]
    risk_category: Optional[str]


class NotificationOut(BaseModel):
    id: int
    patient_id: int
    title: str
    message: str
    type: str
    priority: str
    is_read: bool
    created_at: Optional[datetime]

    class Config:
        orm_mode = True
