import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.repositories.analysis_repo import create_analysis
from app.services.visualization_service import VisualizationService
from pathlib import Path
import numpy as np


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_visualization_generation(tmp_path):
    db = setup_db()
    # create minimal patient/study/image/analysis
    from app.db.models.patient import Patient as P
    from app.db.models.study import Study as S
    from app.db.models.image import Image as Im

    p = P(patient_identifier="pvis", full_name="V1")
    db.add(p); db.commit(); db.refresh(p)
    s = S(patient_id=p.id, accession="SV1")
    db.add(s); db.commit(); db.refresh(s)

    # create a dummy 3D mask (sphere) and save to tmp
    z, y, x = np.mgrid[:64, :64, :64]
    center = np.array([32, 32, 32])
    radius = 18
    mask = ((x - center[2])**2 + (y - center[1])**2 + (z - center[0])**2) < radius**2
    mask_path = tmp_path / "mask.npy"
    np.save(str(mask_path), mask.astype(np.uint8))

    img = Im(study_id=s.id, filename="mask.npy", storage_path=str(mask_path), file_size=mask_path.stat().st_size)
    db.add(img); db.commit(); db.refresh(img)

    an = create_analysis(db, {"study_id": s.id, "image_id": img.id, "model_name": "m", "status": "completed"})

    # use LocalFileStorage mock
    from app.services.storage_service import LocalFileStorage
    class LocalMock(LocalFileStorage):
        def __init__(self, base_dir):
            self.base = Path(base_dir)
            self.base.mkdir(parents=True, exist_ok=True)
        def read_file(self, path):
            return Path(path).read_bytes()
        def save_file(self, data, filename, subpath=None):
            d = self.base / (subpath or "")
            d.mkdir(parents=True, exist_ok=True)
            p = d / filename
            with open(p, "wb") as fh:
                fh.write(data)
            return str(p), p.stat().st_size
        def url_for(self, rel):
            return "file://" + str(rel)

    storage = LocalMock(tmp_path)
    svc = VisualizationService(storage=storage)
    res = svc.generate_visualization(db, an.id, mask_path=str(mask_path))
    assert res is not None
    assert res.get("mesh_rel") is not None
    assert res.get("mask_rel") is not None
    assert res.get("metadata")
    assert res.get("metadata").get("faces") > 0

