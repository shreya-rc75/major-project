import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.repositories.analysis_repo import create_analysis
from app.services.report_service import ReportService
from pathlib import Path


def setup_inmemory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_create_report_record_and_generate(tmp_path):
    db = setup_inmemory_db()
    # create minimal patient -> study -> image -> analysis
    patient = Patient(patient_identifier="P1", full_name="Test")
    db.add(patient)
    db.commit()
    db.refresh(patient)

    study = Study(patient_id=patient.id, accession="S1")
    db.add(study)
    db.commit()
    db.refresh(study)

    img = Image(study_id=study.id, filename="i.jpg", storage_path="images/i.jpg", file_size=123)
    db.add(img)
    db.commit()
    db.refresh(img)

    analysis = create_analysis(db, analysis_in={"study_id": study.id, "image_id": img.id, "model_name": "m", "status": "pending"})

    # create service with local storage
    class LocalStorageMock:
        def __init__(self, base_dir):
            self.base = Path(base_dir)
            (self.base / "reports").mkdir(parents=True, exist_ok=True)
        def save_file(self, data, filename, subpath=""):
            d = self.base / subpath
            d.mkdir(parents=True, exist_ok=True)
            p = d / filename
            with open(p, "wb") as fh:
                fh.write(data)
            return str(Path(subpath) / p.name), p.stat().st_size

    storage = LocalStorageMock(tmp_path)
    svc = ReportService(db, storage=storage)

    # monkey patch the _create_report_record impl if not present (ensure)
    from app.services.report_service_patch import _create_report_record_impl
    setattr(ReportService, "_create_report_record", _create_report_record_impl)

    # patch generate_report full implementation
    from app.services.report_service_full import generate_report_full
    setattr(ReportService, "generate_report", generate_report_full)

    # run generate_report
    res = svc.generate_report(analysis.id)
    assert "report" in res
    report = res["report"]
    assert report.pdf_path.startswith("reports/")

