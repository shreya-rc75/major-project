import io
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.services.report_service import ReportService


class LocalFileStorageMock:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        (self.base_dir / "reports").mkdir(parents=True, exist_ok=True)

    def save_file(self, data: bytes, filename: str, subpath: str = ""):
        # Save under base_dir/subpath/filename
        target_dir = self.base_dir / subpath
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename
        # If file exists, append a counter (shouldn't normally happen because filename has uuid)
        counter = 1
        p = target_path
        while p.exists():
            p = target_dir / f"{filename.rsplit('.pdf',1)[0]}_{counter}.pdf"
            counter += 1
        with open(p, "wb") as fh:
            fh.write(data)
        rel = str(Path(subpath) / p.name)
        return rel, p.stat().st_size


@pytest.fixture(scope="function")
def db_session(tmp_path):
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_store_report_success(db_session, tmp_path):
    storage = LocalFileStorageMock(tmp_path)
    svc = ReportService(db_session, storage=storage)
    pdf = b"%PDF-1.4\n%fakepdfcontent\n" + b"0" * 500
    rel = svc._store_report(123, pdf)
    assert rel.startswith("reports/")
    saved = tmp_path / rel
    assert saved.exists()
    assert saved.stat().st_size == len(pdf)


def test_store_report_empty_pdf(db_session, tmp_path):
    storage = LocalFileStorageMock(tmp_path)
    svc = ReportService(db_session, storage=storage)
    with pytest.raises(RuntimeError):
        svc._store_report(123, b"")


def test_store_report_invalid_analysis_id(db_session, tmp_path):
    storage = LocalFileStorageMock(tmp_path)
    svc = ReportService(db_session, storage=storage)
    pdf = b"%PDF-1.4\ncontent"
    with pytest.raises(RuntimeError):
        svc._store_report(0, pdf)
    with pytest.raises(RuntimeError):
        svc._store_report(-5, pdf)
    with pytest.raises(RuntimeError):
        svc._store_report(None, pdf)  # type: ignore[arg-type]


def test_storage_directory_creation_and_duplicates(db_session, tmp_path):
    storage = LocalFileStorageMock(tmp_path)
    svc = ReportService(db_session, storage=storage)
    pdf = b"%PDF-1.4\ncontent"
    rel1 = svc._store_report(10, pdf)
    rel2 = svc._store_report(10, pdf)
    # Both files should exist and have different names
    assert rel1 != rel2
    assert (tmp_path / rel1).exists()
    assert (tmp_path / rel2).exists()


def test_storage_failure_mocked(db_session, tmp_path, monkeypatch):
    class FailingStorage:
        def save_file(self, data, filename, subpath=None):
            raise IOError("disk full")
    svc = ReportService(db_session, storage=FailingStorage())
    with pytest.raises(RuntimeError):
        svc._store_report(55, b"%PDF-1.4\ncontent")
