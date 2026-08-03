from typing import Dict, Any, List, Optional
from app.db.repositories.dashboard_repo import DashboardRepository
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class DashboardService:
    """Business logic for dashboard metrics computed from repository queries."""

    def __init__(self, db: Session) -> None:
        self.repo = DashboardRepository(db)

    def summary(self) -> Dict[str, Any]:
        counts = self.repo.get_counts()
        avg_conf = self.repo.average_stage_confidence()
        avg_risk = self.repo.average_risk_score()
        high_risk_count = self.repo.high_risk_patient_count()
        stage_dist_rows = self.repo.stage_distribution()
        # convert stage distribution to dict with percentages
        total_stage = sum([c for _, c in stage_dist_rows]) or 1
        stage_dist = [
            {"stage": s, "count": c, "pct": round((c / total_stage) * 100.0, 2)} for s, c in stage_dist_rows
        ]

        risk_dist = self.repo.risk_distribution()

        result = {
            **counts,
            "average_stage_confidence": round(avg_conf, 4),
            "average_risk_3y": round(avg_risk, 4),
            "high_risk_patient_count": high_risk_count,
            "stage_distribution": stage_dist,
            "risk_distribution": risk_dist,
        }
        return result

    def recent(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        return self.repo.recent_analyses(limit=limit, offset=offset)

    def stage_distribution(self) -> List[Dict[str, Any]]:
        rows = self.repo.stage_distribution()
        total = sum([c for _, c in rows]) or 1
        return [{"stage": s, "count": c, "pct": round((c / total) * 100.0, 2)} for s, c in rows]

    def risk_distribution(self) -> Dict[str, int]:
        return self.repo.risk_distribution()

    def monthly_analysis(self, months: int = 12) -> List[Dict[str, Any]]:
        return self.repo.monthly_analysis_counts(months=months)

    def high_risk(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        return self.repo.high_risk_patients(limit=limit, offset=offset)
