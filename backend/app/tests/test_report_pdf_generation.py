import io
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from app.services.report_service import ReportService


@pytest.fixture(scope="module")
def db_session():
    # lightweight in-memory session for ReportService instantiation
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_generate_pdf_success(db_session):
    svc = ReportService(db_session)
    html = "<html><body><h1>Test Report</h1><p>This is a test.</p></body></html>"
    pdf = svc._generate_pdf(html)
    assert isinstance(pdf, (bytes, bytearray))
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 100


def test_generate_pdf_empty_html(db_session):
    svc = ReportService(db_session)
    with pytest.raises(ValueError):
        svc._generate_pdf("")


def test_generate_pdf_invalid_html_type(db_session):
    svc = ReportService(db_session)
    with pytest.raises(ValueError):
        svc._generate_pdf(None)  # type: ignore[arg-type]


def test_generate_pdf_missing_images(db_session, tmp_path):
    svc = ReportService(db_session)
    # HTML references an image that does not exist in the templates folder; WeasyPrint should not fail
    html = '<html><body><h1>Missing Image</h1><img src="nonexistent.png"/></body></html>'
    pdf = svc._generate_pdf(html)
    assert isinstance(pdf, (bytes, bytearray))
    assert pdf.startswith(b"%PDF")


def test_generate_pdf_large_html(db_session):
    svc = ReportService(db_session)
    large_content = "<p>Line</p>" * 2000
    html = f"<html><body><h1>Large Report</h1>{large_content}</body></html>"
    pdf = svc._generate_pdf(html)
    assert isinstance(pdf, (bytes, bytearray))
    assert pdf.startswith(b"%PDF")
    # file should be reasonably sized
    assert len(pdf) > 1000
