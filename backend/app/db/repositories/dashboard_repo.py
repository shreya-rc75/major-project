from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, select
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.models.analysis_result import AnalysisResult
from app.db.models.stage_prediction import StagePrediction
from app.db.models.risk_analysis import RiskAnalysis
from app.db.models.report import Report
from datetime import datetime, timedelta


class DashboardRepository:
    """Repository providing optimized aggregation queries for dashboard metrics."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_counts(self) -> Dict[str, int]:
        total_patients = self.db.query(func.count(Patient.id)).scalar() or 0
        total_studies = self.db.query(func.count(Study.id)).scalar() or 0
        total_images = self.db.query(func.count(Image.id)).scalar() or 0
        total_analyses = self.db.query(func.count(AnalysisResult.id)).scalar() or 0
        total_reports = self.db.query(func.count(Report.id)).scalar() or 0
        return {
            "total_patients": total_patients,
            "total_studies": total_studies,
            "total_images": total_images,
            "total_analyses": total_analyses,
            "total_reports": total_reports,
        }

    def average_stage_confidence(self) -> float:
        # average confidence from stage predictions
        val = self.db.query(func.avg(StagePrediction.confidence)).scalar()
        return float(val or 0.0)

    def average_risk_score(self) -> float:
        # average 3-year risk where available
        val = self.db.query(func.avg(RiskAnalysis.risk_3y)).scalar()
        return float(val or 0.0)

    def high_risk_patient_count(self) -> int:
        # count distinct patients who have at least one risk_analysis with category 'high'
        q = (
            self.db.query(func.count(func.distinct(Study.patient_id)))
            .select_from(RiskAnalysis)
            .join(AnalysisResult, AnalysisResult.id == RiskAnalysis.analysis_id)
            .join(Study, Study.id == AnalysisResult.study_id)
            .filter(RiskAnalysis.risk_category == "high")
        )
        return int(q.scalar() or 0)

    def stage_distribution(self) -> List[Tuple[str, int]]:
        q = (
            self.db.query(StagePrediction.stage, func.count(StagePrediction.id))
            .group_by(StagePrediction.stage)
            .order_by(func.count(StagePrediction.id).desc())
        )
        return [(r[0], int(r[1])) for r in q.all()]

    def risk_distribution(self) -> Dict[str, int]:
        # Return counts for low, medium, high, critical (if present)
        q = (
            self.db.query(RiskAnalysis.risk_category, func.count(RiskAnalysis.id))
            .group_by(RiskAnalysis.risk_category)
        )
        res = {row[0]: int(row[1]) for row in q.all()}
        # ensure keys
        return {
            "low": res.get("low", 0),
            "medium": res.get("medium", 0),
            "high": res.get("high", 0),
            "critical": res.get("critical", 0),
        }

    def monthly_analysis_counts(self, months: int = 12) -> List[Dict[str, Any]]:
        # Use strftime for portability in tests (SQLite). For Postgres you may
        # replace with date_trunc/to_char as needed.
        end = datetime.utcnow().replace(day=1)
        start = (end - timedelta(days=months * 31)).replace(day=1)

        month_col = func.strftime("%Y-%m", AnalysisResult.created_at)
        q = (
            self.db.query(month_col.label("month"), func.count(AnalysisResult.id))
            .filter(AnalysisResult.created_at >= start)
            .group_by("month")
            .order_by("month")
        )
        rows = {r[0]: int(r[1]) for r in q.all()}

        # Build last `months` months list with zero-filling
        out = []
        cur = start
        for i in range(months):
            key = cur.strftime("%Y-%m")
            out.append({"month": key, "count": rows.get(key, 0)})
            # increment month
            if cur.month == 12:
                cur = cur.replace(year=cur.year + 1, month=1)
            else:
                cur = cur.replace(month=cur.month + 1)
        return out

    def recent_analyses(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        # Join AnalysisResult -> Study -> Patient -> StagePrediction -> RiskAnalysis -> Report (left joins)
        ar = AnalysisResult
        sp = StagePrediction
        ra = RiskAnalysis
        st = Study
        p = Patient
        rpt = Report

        q = (
            self.db.query(
                ar.id.label("analysis_id"),
                ar.created_at.label("analysis_date"),
                ar.predicted_class,
                sp.stage,
                ra.risk_category,
                rpt.id.label("report_id"),
                p.full_name.label("patient_name"),
            )
            .join(st, st.id == ar.study_id)
            .join(p, p.id == st.patient_id)
            .outerjoin(sp, sp.analysis_id == ar.id)
            .outerjoin(ra, ra.analysis_id == ar.id)
            .outerjoin(rpt, rpt.analysis_id == ar.id)
            .order_by(ar.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        results = []
        for row in q.all():
            results.append(
                {
                    "analysis_id": row.analysis_id,
                    "patient_name": row.patient_name,
                    "analysis_date": row.analysis_date,
                    "predicted_class": row.predicted_class,
                    "stage": row.stage,
                    "risk_level": row.risk_category,
                    "report_id": row.report_id,
                }
            )
        return results

    def high_risk_patients(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        # Find patients with latest risk categorized as high. We select latest risk per analysis,
        # then pick latest per patient.
        # Subquery: latest risk per analysis is simply RiskAnalysis with max(created_at) per analysis
        subq = (
            self.db.query(
                RiskAnalysis.analysis_id.label("analysis_id"),
                func.max(RiskAnalysis.created_at).label("max_created"),
            )
            .group_by(RiskAnalysis.analysis_id)
            .subquery()
        )

        latest = (
            self.db.query(RiskAnalysis)
            .join(subq, (RiskAnalysis.analysis_id == subq.c.analysis_id) & (RiskAnalysis.created_at == subq.c.max_created))
            .subquery()
        )

        ar = AnalysisResult
        st = Study
        p = Patient

        q = (
            self.db.query(
                p.id.label("patient_id"),
                p.full_name.label("patient_name"),
                latest.c.risk_5y.label("risk_5y"),
                latest.c.risk_category.label("risk_category"),
                latest.c.recommendations.label("recommendations"),
                ar.id.label("analysis_id"),
                ar.created_at.label("analysis_date"),
            )
            .join(ar, ar.id == latest.c.analysis_id)
            .join(st, st.id == ar.study_id)
            .join(p, p.id == st.patient_id)
            .filter(latest.c.risk_category == "high")
            .order_by(latest.c.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        return [
            {
                "patient_id": r.patient_id,
                "patient_name": r.patient_name,
                "latest_analysis_id": r.analysis_id,
                "analysis_date": r.analysis_date,
                "risk_5y": float(r.risk_5y) if r.risk_5y is not None else None,
                "risk_category": r.risk_category,
                "recommendations": r.recommendations,
            }
            for r in q.all()
        ]
