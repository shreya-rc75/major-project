from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app import models
from app.core import security
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

DEMO_OTP = "123456"

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = security.get_password_hash(payload.password)
    user = models.User(email=payload.email, full_name=payload.name, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "User created"}

@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not security.verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # create temp token valid for 10 minutes
    temp_token = security.create_access_token({"sub": str(user.id)}, expires_delta=timedelta(minutes=10))
    return {"temp_token": temp_token, "otp": DEMO_OTP, "user": {"id": user.id, "name": user.full_name, "email": user.email}}

@router.post("/verify-otp")
def verify_otp(token: str, otp: str, db: Session = Depends(get_db)):
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    if otp != DEMO_OTP:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    user_id = int(payload.get("sub"))
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    access_token = security.create_access_token({"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "name": user.full_name, "email": user.email}}

@router.get("/me")
def me(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get('authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    payload = security.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload.get('sub'))
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.full_name, "email": user.email}
