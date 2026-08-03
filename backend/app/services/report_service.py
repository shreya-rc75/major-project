from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import logging

from app.services.storage_service import LocalFileStorage
from app.db.repositories.patient_repo import get_patient
from app.db.repositories.study_repo import get_study
from app.db.repositories.image_repo import get_image
from app.db.repositories.analysis_repo import get_analysis
from app.db.repositories.stage_prediction_repo import get_stage_by_analysis
from app.db.repositories.risk_repo import get_risk_by_analysis
from app.db.repositories.report_repo import get_report

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service responsible for generating PDF reports for analyses.

    This service is intentionally split into discrete steps:
      - collect required data
      - render HTML
      - generate PDF
      - store PDF artifact
      - create Report DB record

    The public API exposes generate_report(...) which orchestrates the flow. The
    individual helper methods are provided to facilitate unit testing and
    separation of concerns.
    """

    def __init__(self, db: Session, storage: Optional[LocalFileStorage] = None) -> None:
        """
        Initialize ReportService.

        Args:
            db: SQLAlchemy Session (scoped/sessionmaker-backed)
            storage: LocalFileStorage instance. If omitted, a default LocalFileStorage
                     will be created using application settings.
        """
        self.db = db
        self.storage = storage or LocalFileStorage()

    def generate_report(self, analysis_id: int) -> Dict[str, Any]:
        """
        High-level orchestration method that will gather data, render the report,
        generate a PDF and persist the report record and artifact.

        NOTE: For the initial implementation only the scaffolding is created —
        the heavy-lifting methods are placeholders. This method will call them
        in sequence. The _collect_report_data implementation is complete and
        validated; subsequent steps are intentionally left for later work.
        """
        data = self._collect_report_data(analysis_id)
        html = self._render_html(data)
        pdf_bytes = self._generate_pdf(html)
        stored_path = self._store_report(analysis_id, pdf_bytes)
        report = self._create_report_record(analysis_id, stored_path)
        return {"report": report, "path": stored_path}

    def _collect_report_data(self, analysis_id: int) -> Dict[str, Any]:
        """
        Collect and validate all data required to render a report for the given analysis.

        The method fetches the following records (and validates their presence):
          - AnalysisResult
          - Study
          - Patient
          - Uploaded Image
          - StagePrediction (optional)
          - RiskAnalysis (optional)

        Returns:
            A structured dictionary containing the objects and derived URLs suitable
            for rendering by a Jinja2 template.

        Raises:
            HTTPException (404) if a required resource is missing.
        """
        # Fetch analysis
        analysis = get_analysis(self.db, analysis_id)
        if not analysis:
            logger.error("AnalysisResult not found for id=%s", analysis_id)
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"AnalysisResult {analysis_id} not found")

        # Fetch study
        study = None
        if getattr(analysis, "study_id", None) is not None:
            study = get_study(self.db, analysis.study_id)
        if not study:
            logger.error("Study not found for analysis id=%s (study_id=%s)", analysis_id, getattr(analysis, "study_id", None))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Study for analysis {analysis_id} not found")

        # Fetch patient
        patient = None
        if getattr(study, "patient_id", None) is not None:
            patient = get_patient(self.db, study.patient_id)
        if not patient:
            logger.error("Patient not found for study id=%s (patient_id=%s)", study.id if study else None, getattr(study, "patient_id", None))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient for study {study.id if study else 'unknown'} not found")

        # Fetch image (uploaded image referenced by analysis)
        image = None
        if getattr(analysis, "image_id", None) is not None:
            image = get_image(self.db, analysis.image_id)
        if not image:
            logger.error("Image not found for analysis id=%s (image_id=%s)", analysis_id, getattr(analysis, "image_id", None))
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Image for analysis {analysis_id} not found")

        # Fetch stage prediction (may be optional)
        stage = get_stage_by_analysis(self.db, analysis_id)

        # Fetch risk analysis (may be optional)
        risk = get_risk_by_analysis(self.db, analysis_id)

        # Optionally fetch any existing Report record for this analysis to link
        existing_report = get_report(self.db, analysis_id)

        # Build URLs for image and gradcam using storage
        image_url = None
        gradcam_url = None
        mask_url = None
        try:
            if image and getattr(image, "storage_path", None):
                image_url = self.storage.url_for(image.storage_path)
            if getattr(analysis, "gradcam_path", None):
                gradcam_url = self.storage.url_for(analysis.gradcam_path)
            # segmentation mask may be stored in a known field (segmentation_path) — if present use it
            if getattr(analysis, "segmentation_path", None):
                mask_url = self.storage.url_for(analysis.segmentation_path)
        except Exception as exc:
            # Do not fail the whole collection just because URL generation failed; log instead
            logger.warning("Could not generate media URL for analysis %s: %s", analysis_id, exc)

        # Structured payload for Jinja rendering
        payload: Dict[str, Any] = {
            "analysis": {
                "id": analysis.id,
                "predicted_class": getattr(analysis, "predicted_class", None),
                "probabilities": getattr(analysis, "probabilities", None),
                "clinical_stage": getattr(analysis, "clinical_stage", None),
                "risk_score": getattr(analysis, "risk_score", None),
                "status": getattr(analysis, "status", None),
                "created_at": getattr(analysis, "created_at", None),
                "updated_at": getattr(analysis, "updated_at", None),
            },
            "study": {
                "id": study.id,
                "accession": getattr(study, "accession", None),
                "clinician": getattr(study, "clinician", None),
                "study_date": getattr(study, "study_date", None),
                "notes": getattr(study, "notes", None),
                "created_at": getattr(study, "created_at", None),
            },
            "patient": {
                "id": patient.id,
                "patient_identifier": getattr(patient, "patient_identifier", None),
                "full_name": getattr(patient, "full_name", None),
                "date_of_birth": getattr(patient, "date_of_birth", None),
                "gender": getattr(patient, "gender", None),
                "contact": getattr(patient, "contact", None),
                "medical_record": getattr(patient, "medical_record", None),
                "created_at": getattr(patient, "created_at", None),
            },
            "image": {
                "id": image.id,
                "filename": getattr(image, "filename", None),
                "storage_path": getattr(image, "storage_path", None),
                "file_size": getattr(image, "file_size", None),
                "mime_type": getattr(image, "mime_type", None),
                "width": getattr(image, "width", None),
                "height": getattr(image, "height", None),
                "preprocessed": getattr(image, "preprocessed", None),
                "uploaded_at": getattr(image, "uploaded_at", None),
                "url": image_url,
            },
            "media": {
                "gradcam_url": gradcam_url,
                "mask_url": mask_url,
            },
            "stage_prediction": None,
            "risk_analysis": None,
            "existing_report": None,
        }

        if stage:
            payload["stage_prediction"] = {
                "stage": getattr(stage, "stage", None),
                "confidence": getattr(stage, "confidence", None),
                "explanation": getattr(stage, "explanation", None),
                "contributing_factors": getattr(stage, "contributing_factors", None),
                "created_at": getattr(stage, "created_at", None),
            }

        if risk:
            payload["risk_analysis"] = {
                "risk_1y": getattr(risk, "risk_1y", None),
                "risk_3y": getattr(risk, "risk_3y", None),
                "risk_5y": getattr(risk, "risk_5y", None),
                "risk_category": getattr(risk, "risk_category", None),
                "confidence": getattr(risk, "confidence", None),
                "recommendations": getattr(risk, "recommendations", None),
                "contributing_factors": getattr(risk, "contributing_factors", None),
                "created_at": getattr(risk, "created_at", None),
            }

        if existing_report:
            payload["existing_report"] = {
                "id": getattr(existing_report, "id", None),
                "pdf_path": getattr(existing_report, "pdf_path", None),
                "created_at": getattr(existing_report, "created_at", None),
            }

        return payload

    def _render_html(self, data: Dict[str, Any]) -> str:
        """Placeholder: render Jinja2 HTML from data"""
        raise NotImplementedError

    def _generate_pdf(self, html: str) -> bytes:
        """Placeholder: convert HTML to PDF bytes"""
        raise NotImplementedError

    def _store_report(self, analysis_id: int, pdf_bytes: bytes) -> str:
        """Placeholder: store PDF using LocalFileStorage and return relative path"""
        raise NotImplementedError

    def _create_report_record(self, analysis_id: int, pdf_storage_path: str) -> Any:
        """Placeholder: create a Report DB record and return it"""
        raise NotImplementedError
