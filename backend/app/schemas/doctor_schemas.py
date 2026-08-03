from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PatientListItem(BaseModel):
    id: int
    patient_identifier: Optional[str]
    full_name: Optional[str]

    class Config:
        orm_mode = True


class PatientDetail(BaseModel):
    patient: dict
    analyses: List[dict]
    reports: List[dict]


class ReportReviewOut(BaseModel):
    id: int
    report_id: int
    doctor_id: int
    status: str
    comment: Optional[str]
    stage_review: Optional[str]
    risk_review: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class ApprovePayload(BaseModel):
    comment: Optional[str] = None
    stage_review: Optional[str] = None
    risk_review: Optional[str] = None


class CommentPayload(BaseModel):
    comment: str
