import pytest
from app.tasks.celery_app import celery_app
from app.tasks.pipeline_tasks import submit_pipeline, _get_progress, preprocess_task
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from pathlib import Path
import time


@pytest.fixture(scope="module", autouse=True)
def configure_celery_environment():
    # Ensure eager mode for tests
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield


def test_pipeline_submit_and_progress(tmp_path):
    # create a fake upload file
    fp = tmp_path / "img.jpg"
    fp.write_bytes(b"fakeimage")

    task_id = submit_pipeline(str(fp), analysis_id=1, clinical_data={})
    assert task_id is not None
    # since eager, final progress should be set
    prog = _get_progress(task_id)
    assert prog is not None
    assert prog.get("status") in ["started", "completed", "queued"] or prog.get("step")


def test_preprocess_task_failures(monkeypatch, tmp_path):
    # force preprocess_image to raise
    monkeypatch.setattr("app.tasks.pipeline_tasks.preprocess_image", lambda path: (_ for _ in ()).throw(Exception("bad file")))
    celery_app.conf.task_always_eager = True
    with pytest.raises(Exception):
        preprocess_task.apply(args=[str(tmp_path / "nofile.jpg")])
