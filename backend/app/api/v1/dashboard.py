from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard_schemas import (
    SummaryResponse,
    RecentAnalysisEntry,
    StageDistributionEntry,
    MonthlyCount,
    HighRiskEntry,
    HighRiskList,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

# auth dependency placeholder - replace with actual JWT auth in your project
try:
    from app.api.deps import get_current_active_user as _get_current_user
except Exception:
    def _get_current_user():
        return None


@router.get("/summary", response_model=SummaryResponse)
def get_summary(db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    try:
        svc = DashboardService(db)
        data = svc.summary()
        # rename total_uploaded_images key to match schema if necessary
        data["total_uploaded_images"] = data.pop("total_images") if "total_images" in data else data.get("total_images", 0)
        return data
    except Exception as exc:
        logger.exception("Failed to compute dashboard summary: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/recent", response_model=List[RecentAnalysisEntry])
def get_recent(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = DashboardService(db)
    try:
        return svc.recent(limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Failed to fetch recent analyses: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/stage-distribution", response_model=List[StageDistributionEntry])
def get_stage_distribution(db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = DashboardService(db)
    try:
        return svc.stage_distribution()
    except Exception as exc:
        logger.exception("Failed to fetch stage distribution: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/risk-distribution")
def get_risk_distribution(db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = DashboardService(db)
    try:
        return svc.risk_distribution()
    except Exception as exc:
        logger.exception("Failed to fetch risk distribution: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/monthly-analysis", response_model=List[MonthlyCount])
def get_monthly(db: Session = Depends(get_db), months: int = 12, current_user: dict = Depends(_get_current_user)):
    svc = DashboardService(db)
    try:
        return svc.monthly_analysis(months=months)
    except Exception as exc:
        logger.exception("Failed to fetch monthly analysis counts: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/high-risk", response_model=List[HighRiskEntry])
def get_high_risk(limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0), db: Session = Depends(get_db), current_user: dict = Depends(_get_current_user)):
    svc = DashboardService(db)
    try:
        return svc.high_risk(limit=limit, offset=offset)
    except Exception as exc:
        logger.exception("Failed to fetch high-risk patients: %s", exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
