import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.repositories.analysis_repo import create_analysis
from app.ai.explainability.explain import ExplainabilityService
from pathlib import Path


@pytest.fixture(scope="module")
def setup_db(tmp_path_factory):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # create a small dummy image in storage by mocking LocalFileStorage
    return session


def test_generate_saliency_and_explanation(monkeypatch, tmp_path):
    # prepare DB and image
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    p = Patient(patient_identifier="px", full_name="P1")
    db.add(p); db.commit(); db.refresh(p)
    s = Study(patient_id=p.id, accession="S1")
    db.add(s); db.commit(); db.refresh(s)
    # create a tiny PNG and save to local temp
    img_path = tmp_path / "i.png"
    import numpy as np
    import cv2
    arr = (np.random.rand(100, 100, 3) * 255).astype('uint8')
    cv2.imwrite(str(img_path), arr)
    img = Image(study_id=s.id, filename="i.png", storage_path=str(img_path), file_size=123)
    db.add(img); db.commit(); db.refresh(img)

    an = create_analysis(db, {"study_id": s.id, "image_id": img.id, "model_name": "m", "status": "completed", "probabilities": {"A": 0.7, "B": 0.3}, "predicted_class": "A"})

    # Use LocalFileStorage mock that treats storage_path as filesystem path
    from app.services.storage_service import LocalFileStorage
    class LocalMock(LocalFileStorage):
        def read_file(self, path):
            return Path(path).read_bytes()
        def save_file(self, data, filename, subpath=None):
            out = tmp_path / "explainability"
            out.mkdir(exist_ok=True)
            p = out / filename
            p.write_bytes(data)
            return str(p), p.stat().st_size
        def url_for(self, rel):
            return "file://" + str(rel)

    svc = ExplainabilityService(storage=LocalMock())
    sal = svc.generate_saliency_map(an.id)
    assert sal is not None
    hist = svc.generate_confidence_histogram(an.id)
    assert hist is not None
    js = svc.generate_explanation_json(an.id)
    assert js is not None

