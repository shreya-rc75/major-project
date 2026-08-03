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


@pytest.fixture(scope="module")
def test_client():
    # create in-memory DB and override get_db dependency
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

    # override auth
    def fake_user():
        return {"id": 42, "role": "doctor", "name": "Dr. Test"}
    try:
        from app.api.deps import get_current_active_user
        app.dependency_overrides[get_current_active_user] = fake_user
    except Exception:
        app.dependency_overrides[lambda: None] = fake_user

    client = TestClient(app)
    yield client


def test_doctor_endpoints_workflow(test_client):
    client = test_client
    # populate DB via a direct session
    from app.db.session import SessionLocal
    db = SessionLocal()
    p = Patient(patient_identifier="D1", full_name="Patient D")
    db.add(p); db.commit(); db.refresh(p)
    s = Study(patient_id=p.id, accession="SD1")
    db.add(s); db.commit(); db.refresh(s)
    img = Image(study_id=s.id, filename="i.jpg", storage_path="/tmp/i.jpg", file_size=123)
    db.add(img); db.commit(); db.refresh(img)
    an = create_analysis(db, {"study_id": s.id, "image_id": img.id, "model_name": "m", "status": "completed"})
    rpt = create_report(db, {"patient_id": p.id, "analysis_id": an.id, "pdf_path": "reports/r1.pdf"})

    # list patients
    r = client.get("/api/v1/doctor/patients")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)

    # get patient detail
    r = client.get(f"/api/v1/doctor/patient/{p.id}")
    assert r.status_code == 200
    pd = r.json()
    assert pd["patient"]["id"] == p.id

    # list reports
    r = client.get("/api/v1/doctor/reports")
    assert r.status_code == 200

    # approve report
    payload = {"comment": "Looks good","stage_review": "Stage II","risk_review": "moderate"}
    r = client.post(f"/api/v1/doctor/report/{rpt.id}/approve", json=payload)
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "approved"

    # comment on report
    r = client.post(f"/api/v1/doctor/report/{rpt.id}/comment", json={"comment": "Add follow-up"})
    assert r.status_code == 200
    j = r.json()
    assert "Add follow-up" in (j.get("comment") or "")

    # reject report
    r = client.post(f"/api/v1/doctor/report/{rpt.id}/reject", json={"comment": "Wrong"})
    assert r.status_code == 200
    j = r.json()
    assert j["status"] == "rejected"

    db.close()
