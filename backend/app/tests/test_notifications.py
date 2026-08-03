import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models.patient import Patient
from app.db.models.study import Study
from app.db.models.image import Image
from app.db.repositories.analysis_repo import create_analysis
from app.services.notification_service import NotificationService
from pathlib import Path


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_notification_create_and_list(tmp_path):
    db = setup_db()
    p = Patient(patient_identifier="p1", full_name="Test", email="test@example.com")
    db.add(p); db.commit(); db.refresh(p)
    svc = NotificationService(db)
    res = svc.send_notification(p.id, "Test", "This is a test", send_email=False)
    assert res["notification"].id > 0
    notes = svc.get_notifications(p.id)
    assert len(notes) == 1


def test_mark_and_delete(tmp_path):
    db = setup_db()
    p = Patient(patient_identifier="p2", full_name="Test2", email="test2@example.com")
    db.add(p); db.commit(); db.refresh(p)
    svc = NotificationService(db)
    res = svc.send_notification(p.id, "T2", "Msg", send_email=False)
    nid = res["notification"].id
    n = svc.mark_read(nid)
    assert n.is_read is True
    assert svc.delete(nid) is True


def test_send_email_mocked(monkeypatch, tmp_path):
    db = setup_db()
    p = Patient(patient_identifier="p3", full_name="Test3", email="test3@example.com")
    db.add(p); db.commit(); db.refresh(p)
    calls = {}
    class FakeEmail:
        def send_email(self, to_address, subject, html_body, plain_body=None):
            calls['to'] = to_address
            calls['subject'] = subject
    svc = NotificationService(db, email_service=FakeEmail())
    res = svc.send_notification(p.id, "EmailTest", "Email body", send_email=True)
    assert res["email_sent"] is True
    assert calls['to'] == p.email
