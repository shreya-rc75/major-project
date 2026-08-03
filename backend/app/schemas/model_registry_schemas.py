from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class ModelCreate(BaseModel):
    model_name: str
    version: str
    framework: Optional[str] = None
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    weights_path: str
    active: Optional[bool] = False


class ModelOut(BaseModel):
    id: int
    model_name: str
    version: str
    framework: Optional[str]
    accuracy: Optional[float]
    precision: Optional[float]
    recall: Optional[float]
    f1_score: Optional[float]
    weights_path: str
    created_at: Optional[datetime]
    active: bool

    class Config:
        orm_mode = True
