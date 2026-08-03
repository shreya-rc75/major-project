from __future__ import annotations
from typing import Any, Dict, Optional
from .celery_app import celery_app
from celery import chain
from celery.utils.log import get_task_logger
import time
import traceback
import os
import json
import redis

from app.services.storage_service import LocalFileStorage
from app.ai.preprocessing.preprocess import preprocess_image
from app.ai.inference.predict import run_inference
from app.ai.inference.gradcam import make_gradcam
from app.ai.clinical.stage_estimator import estimate_stage
from app.ai.risk.risk_model import predict_risk
from app.services.report_service import ReportService
from app.services.notification_service import NotificationService
from app.db.session import SessionLocal

logger = get_task_logger(__name__)

# Redis-based progress reporter
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

PROGRESS_KEY_TEMPLATE = "task:progress:{task_id}"


def _set_progress(task_id: str, step: str, status: str, info: Optional[Dict[str, Any]] = None) -> None:
    key = PROGRESS_KEY_TEMPLATE.format(task_id=task_id)
    payload = {"step": step, "status": status, "timestamp": time.time()}
    if info:
        payload["info"] = info
    try:
        redis_client.set(key, json.dumps(payload), ex=3600)
    except Exception:
        logger.exception("Failed to set progress in Redis for %s", task_id)


def _get_progress(task_id: str) -> Optional[Dict[str, Any]]:
    key = PROGRESS_KEY_TEMPLATE.format(task_id=task_id)
    try:
        v = redis_client.get(key)
        if not v:
            return None
        return json.loads(v)
    except Exception:
        logger.exception("Failed to get progress from Redis for %s", task_id)
        return None


# Timeouts and retry defaults (can be overridden per task)
DEFAULT_TIMEOUT = int(os.getenv("TASK_TIMEOUT_SECONDS", "300"))
DEFAULT_MAX_RETRIES = int(os.getenv("TASK_MAX_RETRIES", "3"))
DEFAULT_RETRY_BACKOFF = int(os.getenv("TASK_RETRY_BACKOFF", "5"))


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': DEFAULT_MAX_RETRIES, 'countdown': DEFAULT_RETRY_BACKOFF}, soft_time_limit=DEFAULT_TIMEOUT)
def preprocess_task(self, upload_path: str) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Preprocess started: %s", upload_path)
    _set_progress(task_id, "preprocess", "started")
    try:
        # actual preprocess implementation; returns processed_path and features
        processed = preprocess_image(upload_path)
        _set_progress(task_id, "preprocess", "completed", {"processed": processed})
        return processed
    except Exception as exc:
        _set_progress(task_id, "preprocess", "failed", {"error": str(exc)})
        logger.exception("Preprocess failed for %s", upload_path)
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': DEFAULT_MAX_RETRIES, 'countdown': DEFAULT_RETRY_BACKOFF}, soft_time_limit=DEFAULT_TIMEOUT)
def inference_task(self, processed_payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Inference started")
    _set_progress(task_id, "inference", "started")
    try:
        result = run_inference(processed_payload)
        _set_progress(task_id, "inference", "completed", {"predicted_class": result.get("predicted_class")})
        return result
    except Exception as exc:
        _set_progress(task_id, "inference", "failed", {"error": str(exc)})
        logger.exception("Inference failed: %s", exc)
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 2, 'countdown': DEFAULT_RETRY_BACKOFF}, soft_time_limit=DEFAULT_TIMEOUT)
def gradcam_task(self, inference_result: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Grad-CAM started")
    _set_progress(task_id, "gradcam", "started")
    try:
        gradcam = make_gradcam(inference_result)
        _set_progress(task_id, "gradcam", "completed", {"gradcam_path": gradcam.get("path")})
        return {**inference_result, **{"gradcam": gradcam}}
    except Exception as exc:
        _set_progress(task_id, "gradcam", "failed", {"error": str(exc)})
        logger.exception("Grad-CAM failed: %s", exc)
        raise


@celery_app.task(bind=True)
def stage_prediction_task(self, inference_with_gradcam: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Stage prediction started")
    _set_progress(task_id, "stage_prediction", "started")
    try:
        clinical_data = inference_with_gradcam.get("clinical_data", {})
        probs = inference_with_gradcam.get("probabilities", {})
        per_cell = inference_with_gradcam.get("per_cell_features")
        stage = estimate_stage(clinical_data, probs, per_cell)
        _set_progress(task_id, "stage_prediction", "completed", {"stage": stage.get("stage")})
        return {**inference_with_gradcam, **{"stage_prediction": stage}}
    except Exception as exc:
        _set_progress(task_id, "stage_prediction", "failed", {"error": str(exc)})
        logger.exception("Stage prediction failed: %s", exc)
        raise


@celery_app.task(bind=True)
def risk_prediction_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Risk prediction started")
    _set_progress(task_id, "risk_prediction", "started")
    try:
        clinical_data = payload.get("clinical_data", {})
        probs = payload.get("probabilities", {})
        per_cell = payload.get("per_cell_features")
        risk = predict_risk(clinical_data, probs, per_cell)
        _set_progress(task_id, "risk_prediction", "completed", {"risk_category": risk.get("risk_category")})
        return {**payload, **{"risk_prediction": risk}}
    except Exception as exc:
        _set_progress(task_id, "risk_prediction", "failed", {"error": str(exc)})
        logger.exception("Risk prediction failed: %s", exc)
        raise


@celery_app.task(bind=True)
def db_save_task(self, analysis_payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("DB save started")
    _set_progress(task_id, "db_save", "started")
    try:
        # Persist AnalysisResult and related artifacts using services
        db = SessionLocal()
        from app.services.analysis_service import run_analysis_and_persist
        # run_analysis_and_persist will handle transactional persistence of analysis, stage, risk
        res = run_analysis_and_persist(db, analysis_payload.get("analysis_id"), analysis_payload, analysis_payload.get("clinical_data"))
        db.close()
        _set_progress(task_id, "db_save", "completed", {"analysis_id": res.get("analysis_id")})
        return {**analysis_payload, **{"db_result": res}}
    except Exception as exc:
        _set_progress(task_id, "db_save", "failed", {"error": str(exc)})
        logger.exception("DB save failed: %s", exc)
        raise


@celery_app.task(bind=True)
def generate_report_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Report generation started")
    _set_progress(task_id, "report_generation", "started")
    try:
        db = SessionLocal()
        rs = ReportService(db)
        analysis_id = payload.get("analysis_id")
        report_res = rs.generate_report(analysis_id)
        db.close()
        _set_progress(task_id, "report_generation", "completed", {"report_id": report_res.get("report").id if report_res.get("report") else None})
        return {**payload, **{"report": report_res}}
    except Exception as exc:
        _set_progress(task_id, "report_generation", "failed", {"error": str(exc)})
        logger.exception("Report generation failed: %s", exc)
        raise


@celery_app.task(bind=True)
def store_pdf_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Store PDF started")
    _set_progress(task_id, "store_pdf", "started")
    try:
        # In our flow, generate_report already stored PDF and created report record; pass-through
        _set_progress(task_id, "store_pdf", "completed")
        return payload
    except Exception as exc:
        _set_progress(task_id, "store_pdf", "failed", {"error": str(exc)})
        logger.exception("Store PDF failed: %s", exc)
        raise


@celery_app.task(bind=True)
def send_notification_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Send notification started")
    _set_progress(task_id, "send_notification", "started")
    try:
        db = SessionLocal()
        ns = NotificationService(db)
        analysis_id = payload.get("analysis_id")
        # For simplicity, send doctor review required if high risk, else report generated notification
        risk = payload.get("risk_prediction", {}).get("risk_category")
        if risk == "high":
            res = ns.notify_high_risk(analysis_id, send_email=True)
        else:
            # if report exists, notify report generated
            rpt = payload.get("report")
            if rpt and rpt.get("report"):
                ns.notify_report_generated(rpt.get("report").id, send_email=False)
                res = {"notification_created": True}
            else:
                res = {"notification_created": False}
        db.close()
        _set_progress(task_id, "send_notification", "completed", {"result": res})
        return {**payload, **{"notification_result": res}}
    except Exception as exc:
        _set_progress(task_id, "send_notification", "failed", {"error": str(exc)})
        logger.exception("Send notification failed: %s", exc)
        raise


@celery_app.task(bind=True)
def complete_task(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    task_id = self.request.id
    logger.info("Pipeline complete for task %s", task_id)
    _set_progress(task_id, "complete", "completed", {"final_payload": payload})
    return {"status": "completed", "payload": payload}


def submit_pipeline(upload_path: str, analysis_id: int, clinical_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Entrypoint to submit the full pipeline. Returns the Celery parent task id.

    Pipeline steps:
      preprocess -> inference -> gradcam -> stage_prediction -> risk_prediction -> db_save -> generate_report -> store_pdf -> send_notification -> complete
    """
    # We'll pass a payload object through the chain
    initial_payload = {"upload_path": upload_path, "analysis_id": analysis_id, "clinical_data": clinical_data}
    parent = (
        preprocess_task.s(upload_path)
        | inference_task.s()
        | gradcam_task.s()
        | stage_prediction_task.s()
        | risk_prediction_task.s()
        | db_save_task.s()
        | generate_report_task.s()
        | store_pdf_task.s()
        | send_notification_task.s()
        | complete_task.s()
    )
    res = parent.apply_async()
    logger.info("Submitted pipeline with root task id %s", res.id)
    # initialize progress
    _set_progress(res.id, "queued", "started", {"upload_path": upload_path, "analysis_id": analysis_id})
    return res.id
