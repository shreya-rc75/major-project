"""Authentication endpoints (register, login, token validation)."""
import logging
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.core.exceptions import (
    AuthenticationException,
    ConflictException,
    ValidationException,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user.
    
    Args:
        user_in: Registration data (email, full_name, password)
        db: Database session
    
    Returns:
        Created user information
    
    Raises:
        ConflictException: If email already registered
        ValidationException: If validation fails
    """
    try:
        # Check if user already exists
        existing = db.query(models.User).filter(
            models.User.email == user_in.email
        ).first()
        if existing:
            raise ConflictException(
                detail=f"Email '{user_in.email}' already registered"
            )
        
        # Validate password strength (minimum requirements)
        if len(user_in.password) < 6:
            raise ValidationException(
                detail="Password must be at least 6 characters long"
            )
        
        # Create new user
        user = models.User(
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=get_password_hash(user_in.password),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User registered: {user.email}")
        return user
    
    except ConflictException:
        raise
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.rollback()
        raise ValidationException(detail="Failed to register user")


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with email and password.
    
    Args:
        form_data: Email (username) and password
        db: Database session
    
    Returns:
        Access token and token type
    
    Raises:
        AuthenticationException: If credentials are invalid
    """
    try:
        # Find user by email
        user = db.query(models.User).filter(
            models.User.email == form_data.username
        ).first()
        
        # Verify credentials
        if not user or not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for: {form_data.username}")
            raise AuthenticationException(
                detail="Incorrect email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            raise AuthenticationException(
                detail="User account is inactive"
            )
        
        # Create access token
        access_token = create_access_token(data={"sub": user.email})
        logger.info(f"User logged in: {user.email}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise AuthenticationException(detail="Login failed")


def get_current_user(
    token: str = Depends(__import__('fastapi.security', fromlist=['OAuth2PasswordBearer']).OAuth2PasswordBearer(tokenUrl="/auth/login")),
    db: Session = Depends(get_db)
) -> models.User:
    """Validate JWT token and return current user.
    
    This dependency should be used on protected endpoints.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
    
    Returns:
        Current authenticated user
    
    Raises:
        AuthenticationException: If token is invalid or user not found
    """
    # Import here to avoid circular imports
    from fastapi.security import OAuth2PasswordBearer
    
    credentials_exception = AuthenticationException(
        detail="Could not validate credentials"
    )
    
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise credentials_exception
        
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
    except Exception:
        raise credentials_exception
    
    user = db.query(models.User).filter(
        models.User.email == email
    ).first()
    
    if user is None:
        raise credentials_exception
    
    return user
