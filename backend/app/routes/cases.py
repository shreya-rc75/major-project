from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from ..database import get_session
from ..models import Case, Image
from pydantic import BaseModel
from typing import Optional
from ..ml.predictor import score_from_data
import os
import time

UPLOAD_DIR = "backend/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/api/cases", tags=["cases"])

class CaseCreate(BaseModel):
    patient_id: int
    created_by: int
    clinical_data: Optional[str]

@router.post("/")
def create_case(payload: CaseCreate, session: Session = Depends(get_session)):
    case = Case(**payload.dict())
    session.add(case)
    session.commit()
    session.refresh(case)
    return case

@router.post("/{case_id}/image")
async def upload_image(case_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    # validate file extension and size
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg"]:
        raise HTTPException(status_code=400, detail="Invalid file type")
    contents = await file.read()
    max_size = 5 * 1024 * 1024  # 5 MB
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    safe_ts = int(time.time())
    safe_name = f"case_{case_id}_{safe_ts}{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)
    try:
        with open(dest, "wb") as buffer:
            buffer.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    img = Image(case_id=case_id, filename=filename, filepath=dest, file_type=file.content_type, file_size=os.path.getsize(dest))
    session.add(img)
    session.commit()
    session.refresh(img)
    return img

@router.get("/")
def list_cases(session: Session = Depends(get_session)):
    cases = session.exec(select(Case)).all()
    return cases

@router.get("/{case_id}")
def get_case(case_id: int, session: Session = Depends(get_session)):
    case = session.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case
