# backend/app/main.py
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# import routers
from app.api.v1 import patient as patient_router
from app.api.v1 import doctor as doctor_router
from app.api.v1 import explainability as explain_router
from app.api.v1 import visualization as visualization_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title="Major Project API")

    # CORS
    origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # include routers
    app.include_router(patient_router.router)
    app.include_router(doctor_router.router)
    app.include_router(explain_router.router)
    app.include_router(visualization_router.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
