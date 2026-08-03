import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.services.model_registry_service import ModelRegistryService
from app.db.models.patient import Patient
import os


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_model_registry_crud(tmp_path):
    db = setup_db()
    svc = ModelRegistryService(db)
    model = svc.register_model({
        "model_name": "effnet",
        "version": "v1",
        "framework": "pytorch",
        "accuracy": 0.9,
        "precision": 0.88,
        "recall": 0.87,
        "f1_score": 0.875,
        "weights_path": str(tmp_path / "m.pt"),
        "active": False,
    })
    assert model.id is not None
    listed = svc.list_models()
    assert len(listed) >= 1

    # set active
    svc.set_active(model.id)
    active = svc.get_active()
    assert active.id == model.id

    # load active model (will fallback to weights_path string)
    loaded = svc.load_active_model()
    assert loaded == model.weights_path or loaded is not None

    # update
    svc.update_model(model.id, {"accuracy": 0.91})
    m2 = svc.get_model(model.id)
    assert round(m2.accuracy, 2) == 0.91

    # delete
    assert svc.delete_model(model.id) is True

