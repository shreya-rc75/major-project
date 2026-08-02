from typing import Optional, List, Dict
from pydantic import BaseModel, EmailStr
from datetime import datetime

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str]

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

# --- Patient ---
class PatientBase(BaseModel):
    name: str
    age: Optional[int]
    phone: Optional[str]
    email: Optional[EmailStr]
    address: Optional[str]
    blood_group: Optional[str]
    previous_diagnosis: Optional[str]
    smoking: Optional[bool]
    hpv_status: Optional[str]
    family_history: Optional[str]
    symptoms: Optional[str]

class PatientCreate(PatientBase):
    pass

class PatientOut(PatientBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

# --- Prediction / Report ---
class PredictionOut(BaseModel):
    prediction: str
    confidence: float
    probabilities: Dict[str, float]
    gradcam_url: Optional[str]

class ReportOut(BaseModel):
    id: int
    patient_id: int
    prediction: str
    confidence: float
    created_at: datetime

    class Config:
        orm_mode = True
