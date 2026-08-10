from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select
from ..database import get_session
from ..models import User
from ..auth import get_password_hash, verify_password, create_access_token, decode_token
from pydantic import BaseModel
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/signup")
def signup(payload: SignupRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(name=payload.name, email=payload.email, password_hash=get_password_hash(payload.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"message": "User created"}

@router.post("/login")
def login(payload: LoginRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == payload.email)).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    # For demo: return a temp token and OTP code
    temp_token = create_access_token({"sub": str(user.id), "otp_required": True}, expires_delta=timedelta(minutes=10))
    # demo OTP
    otp = "123456"
    return {"temp_token": temp_token, "otp": otp, "user": {"id": user.id, "name": user.name, "email": user.email}}

@router.post("/verify-otp")
def verify_otp(token: str, otp: str, session: Session = Depends(get_session)):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    if otp != "123456":
        raise HTTPException(status_code=400, detail="Invalid OTP")
    access_token = create_access_token({"sub": payload.get("sub")})
    # return user info
    user = session.get(User, int(payload.get("sub")))
    return {"access_token": access_token, "token_type": "bearer", "user": {"id": user.id, "name": user.name, "email": user.email}}

@router.get("/me")
def me(request: Request, session: Session = Depends(get_session)):
    auth_header = request.headers.get('authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = parts[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = session.get(User, int(payload.get('sub')))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "name": user.name, "email": user.email}
