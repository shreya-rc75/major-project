"""FastAPI application factory and configuration."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.database import init_db
# Import API routers
from app.api import auth, patients

# Note: other API modules (cases, predictions, reports, dashboard) will be imported
# below after they are created to ensure the /api prefix is used consistently.

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="CerviVal - Cervical Cancer Detection AI",
    description="AI-powered clinical decision support system for cervical cancer screening",
    version="0.1.0",
)

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize database: {e}")
    raise

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info(f"CORS configured for origins: {settings.ALLOWED_ORIGINS}")

# Include routers under /api prefix to match frontend
app.include_router(auth.router, prefix="/api")
app.include_router(patients.router, prefix="/api")

# Import and include the remaining routers (cases, predictions, reports, dashboard)
# These modules will be present in app.api package.
try:
    from app.api import cases, predictions, reports, dashboard
    app.include_router(cases.router, prefix="/api")
    app.include_router(predictions.router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(dashboard.router, prefix="/api")
except Exception as e:
    logger.warning(f"Optional API modules not available at startup: {e}")


# Global error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Internal server error",
            "status_code": 500,
        },
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"][1:]),
            "message": error["msg"],
        })
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "Validation error",
            "status_code": 422,
            "details": errors,
        },
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


# Health check endpoints
@app.get("/", tags=["system"])  # root
def read_root():
    """Root health check."""
    return {
        "status": "ok",
        "application": "CerviVal Backend",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["system"])
def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "database": "connected",
        "environment": settings.ENVIRONMENT,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development",
    )
