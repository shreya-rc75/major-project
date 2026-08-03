import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.repositories.analysis_repo import create_analysis
from app.db.repositories.stage_prediction_repo import create_stage_prediction
from app.db.repositories.risk_repo import create_risk_analysis
from app.db.repositories.report_repo import create_report
from app.services.dashboard_service import DashboardService
from datetime import datetime, timedelta


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_dashboard_summary_and_distributions():
    db = setup_db()
    # create patients/studies/images/analyses
    p1 = Patient(patient_identifier="P1", full_name="Alice")
    p2 = Patient(patient_identifier="P2", full_name="Bob")
    db.add_all([p1, p2])
    db.commit()
    db.refresh(p1); db.refresh(p2)

    s1 = Study(patient_id=p1.id, accession="S1")
    s2 = Study(patient_id=p2.id, accession="S2")
    db.add_all([s1, s2]); db.commit(); db.refresh(s1); db.refresh(s2)

    img1 = Image(study_id=s1.id, filename="a.jpg", storage_path="p/a.jpg", file_size=100)
    img2 = Image(study_id=s2.id, filename="b.jpg", storage_path="p/b.jpg", file_size=200)
    db.add_all([img1, img2]); db.commit(); db.refresh(img1); db.refresh(img2)

    ar1 = create_analysis(db, {"study_id": s1.id, "image_id": img1.id, "model_name": "m", "status": "completed"})
    ar2 = create_analysis(db, {"study_id": s2.id, "image_id": img2.id, "model_name": "m", "status": "completed"})

    # create stage predictions
    sp1 = create_stage_prediction(db, {"analysis_id": ar1.id, "stage": "Stage II", "confidence": 0.7, "explanation": "ok", "contributing_factors": []})
    sp2 = create_stage_prediction(db, {"analysis_id": ar2.id, "stage": "Stage III", "confidence": 0.9, "explanation": "ok", "contributing_factors": []})

    # risk analyses
    ra1 = create_risk_analysis(db, {"analysis_id": ar1.id, "risk_1y": 0.02, "risk_3y": 0.05, "risk_5y": 0.1, "risk_category": "low", "confidence": 0.4, "recommendations": [], "contributing_factors": []})
    ra2 = create_risk_analysis(db, {"analysis_id": ar2.id, "risk_1y": 0.4, "risk_3y": 0.6, "risk_5y": 0.8, "risk_category": "high", "confidence": 0.85, "recommendations": ["Refer"], "contributing_factors": []})

    # report for ar1
    rep = create_report(db, {"patient_id": p1.id, "analysis_id": ar1.id, "pdf_path": "reports/r1.pdf"})

    svc = DashboardService(db)
    summary = svc.summary()
    assert summary["total_patients"] == 2
    assert summary["total_studies"] == 2
    assert summary["total_images"] == 2
    assert summary["total_analyses"] == 2
    assert summary["total_reports"] == 1
    assert summary["average_stage_confidence"] > 0
    assert summary["average_risk_3y"] > 0

    recent = svc.recent()
    assert len(recent) == 2

    stage_dist = svc.stage_distribution()
    assert any(d["stage"] == "Stage II" for d in stage_dist)

    risk_dist = svc.risk_distribution()
    assert risk_dist["high"] >= 1

    monthly = svc.monthly_analysis()
    assert isinstance(monthly, list)

    high_risk = svc.high_risk()
    assert len(high_risk) >= 1
