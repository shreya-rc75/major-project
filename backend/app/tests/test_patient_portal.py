import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.main import app
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.repositories.analysis_repo import create_analysis
from app.db.repositories.report_repo import create_report
from app.db.repositories.notification_repo import create_notification
from app.db.repositories.risk_repo import create_risk_analysis


@pytest.fixture(scope="module")
def test_client():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def get_test_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides = {}
    from app.db.session import get_db
    app.dependency_overrides[get_db] = get_test_db

    # fake patient auth
    def fake_patient():
        return {"id": 100, "role": "patient", "patient_id": 100}
    try:
        from app.api.deps import get_current_active_user
        app.dependency_overrides[get_current_active_user] = fake_patient
    except Exception:
        app.dependency_overrides[lambda: None] = fake_patient

    client = TestClient(app)
    yield client


def test_patient_portal_endpoints(test_client, tmp_path):
    client = test_client
    from app.db.session import SessionLocal
    db = SessionLocal()

    # create patient and related records
    p = Patient(patient_identifier="P100", full_name="Patient101")
    db.add(p); db.commit(); db.refresh(p)

    s = Study(patient_id=p.id, accession="S100")
    db.add(s); db.commit(); db.refresh(s)

    img = Image(study_id=s.id, filename="i.jpg", storage_path="/tmp/i.jpg", file_size=10)
    db.add(img); db.commit(); db.refresh(img)

    an = create_analysis(db, {"study_id": s.id, "image_id": img.id, "model_name": "m", "status": "completed", "predicted_class": "A", "probabilities": {"A":0.8, "B":0.2}})
    rpt = create_report(db, {"patient_id": p.id, "analysis_id": an.id, "pdf_path": "reports/r100.pdf"})
    create_notification(db, {"patient_id": p.id, "title": "Test", "message": "Msg", "type": "info", "priority": "normal"})
    create_risk_analysis(db, {"analysis_id": an.id, "risk_1y": 0.01, "risk_3y": 0.02, "risk_5y": 0.03, "risk_category": "low"})

    # override fake patient id to match created patient
    def fake_patient_override():
        return {"id": 200, "role": "patient", "patient_id": p.id}
    from app.api.deps import get_current_active_user as dep
    app.dependency_overrides[dep] = fake_patient_override

    # profile
    r = client.get("/api/v1/patient/profile")
    assert r.status_code == 200
    jp = r.json()
    assert jp["id"] == p.id

    # history
    r = client.get("/api/v1/patient/history")
    assert r.status_code == 200
    hist = r.json()
    assert isinstance(hist, list) and len(hist) >= 1

    # reports
    r = client.get("/api/v1/patient/reports")
    assert r.status_code == 200
    reps = r.json()
    assert isinstance(reps, list) and len(reps) >= 1

    # risk history
    r = client.get("/api/v1/patient/risk-history")
    assert r.status_code == 200
    rh = r.json()
    assert isinstance(rh, list)

    # notifications
    r = client.get("/api/v1/patient/notifications")
    assert r.status_code == 200
    notes = r.json()
    assert isinstance(notes, list) and len(notes) >= 1

    # download report
    # mock storage read by monkeypatching LocalFileStorage.read_file
    from app.services.storage_service import LocalFileStorage
    orig_read = LocalFileStorage.read_file
    def fake_read(self, path):
        return b"PDFBYTES"
    LocalFileStorage.read_file = fake_read
    r = client.get(f"/api/v1/patient/reports/download/{rpt.id}")
    assert r.status_code == 200
    assert r.content == b"PDFBYTES"
    # restore
    LocalFileStorage.read_file = orig_read

    db.close()
