from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.db.repositories.notification_repo import (
    create_notification as repo_create,
    get_notifications_for_patient,
    get_notification as repo_get_notification,
    mark_notification_as_read as repo_mark_read,
    delete_notification as repo_delete,
)
from app.db.repositories.patient_repo import get_patient
from app.db.repositories.analysis_repo import get_analysis
from app.db.repositories.report_repo import get_report
from app.services.email_service import EmailService
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles creating notifications and dispatching via email.

    This service is designed to be used by other services as an event target
    (e.g., when a report is generated or a high-risk event is detected).
    """

    def __init__(self, db: Session, email_service: Optional[EmailService] = None) -> None:
        self.db = db
        self.email = email_service or EmailService()

    def send_notification(self, patient_id: int, title: str, message: str, type: str = "info", priority: str = "normal", send_email: bool = False) -> Dict[str, Any]:
        # validate patient exists
        patient = get_patient(self.db, patient_id)
        if not patient:
            logger.error("Attempt to send notification for non-existent patient_id=%s", patient_id)
            raise RuntimeError("Patient not found")

        n = repo_create(self.db, {
            "patient_id": patient_id,
            "title": title,
            "message": message,
            "type": type,
            "priority": priority,
        })

        if send_email and getattr(patient, "email", None):
            try:
                self.email.send_email(
                    to_address=patient.email,
                    subject=title,
                    html_body=message,
                )
            except Exception as exc:
                logger.exception("Failed to send notification email to %s: %s", patient.email, exc)
                # do not fail creation; surface partial failure in return
                return {"notification": n, "email_sent": False, "error": str(exc)}

        return {"notification": n, "email_sent": bool(send_email and getattr(patient, "email", None))}

    def get_notifications(self, patient_id: int, limit: int = 50, offset: int = 0):
        return get_notifications_for_patient(self.db, patient_id, limit=limit, offset=offset)

    def mark_read(self, notification_id: int):
        n = repo_get_notification(self.db, notification_id)
        if not n:
            raise RuntimeError("Notification not found")
        return repo_mark_read(self.db, n)

    def delete(self, notification_id: int):
        n = repo_get_notification(self.db, notification_id)
        if not n:
            raise RuntimeError("Notification not found")
        repo_delete(self.db, n)
        return True

    # Triggers
    def notify_high_risk(self, analysis_id: int, send_email: bool = True) -> Dict[str, Any]:
        analysis = get_analysis(self.db, analysis_id)
        if not analysis:
            raise RuntimeError("Analysis not found")
        report = get_report(self.db, analysis_id)
        # find patient via study
        patient_id = None
        if getattr(analysis, "study_id", None):
            from app.db.repositories.study_repo import get_study
            st = get_study(self.db, analysis.study_id)
            if st:
                patient_id = st.patient_id
        if not patient_id:
            raise RuntimeError("Patient not found for analysis")

        title = "High-Risk Alert: Immediate Attention Recommended"
        message = (
            f"Our system has identified a high 5-year progression risk for patient ID {patient_id} "
            f"from analysis {analysis_id}. Please review the case and consider expedited clinical follow-up."
        )
        return self.send_notification(patient_id, title, message, type="alert", priority="high", send_email=send_email)

    def notify_report_generated(self, report_id: int, send_email: bool = False) -> Dict[str, Any]:
        from app.db.repositories.report_repo import get_report as repo_get
        rpt = repo_get(self.db, report_id)
        if not rpt:
            raise RuntimeError("Report not found")
        patient_id = rpt.patient_id
        title = "New Analysis Report Available"
        message = f"A new analysis report (ID: {rpt.id}) is available for patient ID {patient_id}."
        return self.send_notification(patient_id, title, message, type="info", priority="normal", send_email=send_email)

    def notify_analysis_completed(self, analysis_id: int, send_email: bool = False) -> Dict[str, Any]:
        analysis = get_analysis(self.db, analysis_id)
        if not analysis:
            raise RuntimeError("Analysis not found")
        patient_id = None
        if getattr(analysis, "study_id", None):
            from app.db.repositories.study_repo import get_study
            st = get_study(self.db, analysis.study_id)
            if st:
                patient_id = st.patient_id
        if not patient_id:
            raise RuntimeError("Patient not found for analysis")
        title = "Analysis Completed"
        message = f"An automated analysis (ID: {analysis_id}) has completed for patient {patient_id}."
        return self.send_notification(patient_id, title, message, type="info", priority="normal", send_email=send_email)

    def notify_doctor_review_required(self, analysis_id: int, send_email: bool = True) -> Dict[str, Any]:
        analysis = get_analysis(self.db, analysis_id)
        if not analysis:
            raise RuntimeError("Analysis not found")
        patient_id = None
        if getattr(analysis, "study_id", None):
            from app.db.repositories.study_repo import get_study
            st = get_study(self.db, analysis.study_id)
            if st:
                patient_id = st.patient_id
        if not patient_id:
            raise RuntimeError("Patient not found for analysis")
        title = "Clinician Review Required"
        message = f"Analysis {analysis_id} requires clinician review for patient {patient_id}. Please review the case." 
        return self.send_notification(patient_id, title, message, type="action_required", priority="high", send_email=send_email)
