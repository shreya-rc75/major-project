import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.repositories.analysis_repo import create_analysis
from app.services.analysis_service import run_analysis_and_persist

# Use SQLite memory DB for integration tests

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.close()


def test_full_analysis_flow(db_session):
    # Create patient
    patient = Patient(patient_identifier="P123", full_name="Test Patient")
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)

    # Create study
    study = Study(patient_id=patient.id, accession="S123")
    db_session.add(study)
    db_session.commit()
    db_session.refresh(study)

    # Create image
    img = Image(study_id=study.id, filename="img.jpg", storage_path="path/to/img.jpg", file_size=1234)
    db_session.add(img)
    db_session.commit()
    db_session.refresh(img)

    # Create pending analysis
    analysis = create_analysis(db_session, analysis_in={
        "study_id": study.id,
        "image_id": img.id,
        "model_name": "test-model",
        "status": "pending",
    })

    # Mock model inference result
    model_result = {
        "predicted_class": "cancer",
        "probabilities": {"normal": 0.01, "low_grade": 0.01, "high_grade": 0.08, "cancer": 0.9},
        "per_cell_features": [{"mean_nucleus_area": 500, "solidity": 0.4}],
        # gradcam bytes omitted for test
    }

    # Run persistence (synchronously)
    res = run_analysis_and_persist(db_session, analysis_id=analysis.id, model_inference_result=model_result, clinical_data={"biopsy": "invasive carcinoma", "hpv": "positive"})
    assert res.get("status") == "completed"

    # Check AnalysisResult updated
    ar = db_session.query("analysis_results").filter_by(id=analysis.id).first()
    # since we used raw SQLAlchemy table, use query on model instead
    from app.db.models.analysis_result import AnalysisResult
    ar_obj = db_session.query(AnalysisResult).filter(AnalysisResult.id == analysis.id).one_or_none()
    assert ar_obj is not None
    assert ar_obj.status == "completed"
    assert ar_obj.clinical_stage is not None

    # Check StagePrediction exists
    from app.db.models.stage_prediction import StagePrediction
    sp = db_session.query(StagePrediction).filter(StagePrediction.analysis_id == analysis.id).one_or_none()
    assert sp is not None

    # Check RiskAnalysis exists
    from app.db.models.risk_analysis import RiskAnalysis
    rk = db_session.query(RiskAnalysis).filter(RiskAnalysis.analysis_id == analysis.id).one_or_none()
    assert rk is not None
    assert rk.risk_category in ["low", "medium", "high"]
