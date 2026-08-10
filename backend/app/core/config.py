"""Application configuration from environment variables."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./cervicare_dev.db"
    )
    
    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "dev-key-change-in-production-12345"
    )
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    )
    
    # CORS
    ALLOWED_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
        ).split(",")
    ]
    
    # AI Model
    MODEL_PATH: str = os.getenv(
        "MODEL_PATH",
        "./models/efficientnet_b3_best.pth"
    )
    
    # File uploads
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Validation
    def validate_production(self) -> bool:
        """Check if critical production settings are configured."""
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == "dev-key-change-in-production-12345":
                raise ValueError(
                    "CRITICAL: SECRET_KEY not changed for production! "
                    "Set SECRET_KEY environment variable."
                )
            if not self.DATABASE_URL.startswith("postgresql://"):
                raise ValueError(
                    "CRITICAL: PostgreSQL required for production. "
                    "Set DATABASE_URL to a PostgreSQL connection string."
                )
        return True

settings = Settings()
settings.validate_production()
