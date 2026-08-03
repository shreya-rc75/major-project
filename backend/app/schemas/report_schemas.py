from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportOut(BaseModel):
    id: int
    patient_id: int
    analysis_id: int
    pdf_path: str
    html_path: Optional[str]
    report_status: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
