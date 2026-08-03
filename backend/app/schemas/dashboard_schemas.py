from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class SummaryResponse(BaseModel):
    total_patients: int
    total_studies: int
    total_uploaded_images: int
    total_analyses: int
    total_reports: int
    average_stage_confidence: float
    average_risk_3y: float
    high_risk_patient_count: int
    stage_distribution: List[Dict[str, Any]]
    risk_distribution: Dict[str, int]


class RecentAnalysisEntry(BaseModel):
    analysis_id: int
    patient_name: Optional[str]
    analysis_date: Optional[datetime]
    predicted_class: Optional[str]
    stage: Optional[str]
    risk_level: Optional[str]
    report_id: Optional[int]


class StageDistributionEntry(BaseModel):
    stage: str
    count: int
    pct: float


class MonthlyCount(BaseModel):
    month: str
    count: int


class HighRiskEntry(BaseModel):
    patient_id: int
    patient_name: Optional[str]
    latest_analysis_id: int
    analysis_date: Optional[datetime]
    risk_5y: Optional[float]
    risk_category: Optional[str]
    recommendations: Optional[List[str]]


class HighRiskList(BaseModel):
    total: int
    results: List[HighRiskEntry]
