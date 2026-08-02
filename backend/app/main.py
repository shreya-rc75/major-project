import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .api import auth, patients, predict

# Create DB tables automatically for scaffold; in production use Alembic
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CerviCare AI - Backend", version="0.1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to frontend origin in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(predict.router)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cervicare")

@app.get("/")
def read_root():
    return {"msg": "CerviCare AI Backend is running"}
