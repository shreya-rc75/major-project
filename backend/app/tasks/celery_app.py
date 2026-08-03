import os
from celery import Celery
from celery.signals import worker_ready
import logging
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

CELERY_BROKER = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
CELERY_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER)

celery_app = Celery("app.tasks", broker=CELERY_BROKER, backend=CELERY_BACKEND)

# Default task settings; individual tasks may override
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_default_rate_limit=None,
)

# Optional eager mode for testing
if os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() in ["1", "true", "yes"]:
    celery_app.conf.task_always_eager = True


@worker_ready.connect
def on_worker_ready(**kwargs):
    """Perform basic validations when the worker starts: DB connectivity and model/paths.

    This helps surface misconfiguration early instead of at runtime.
    """
    logger.info("Celery worker ready — running startup validations")
    # DB connectivity
    try:
        db = SessionLocal()
        db.execute('SELECT 1')
        db.close()
        logger.info("Database connectivity OK")
    except Exception as exc:
        logger.exception("Database connectivity check failed: %s", exc)

    # Check model weights path if provided
    model_path = os.getenv("MODEL_WEIGHTS_PATH")
    if model_path:
        try:
            if not os.path.exists(model_path):
                logger.warning("MODEL_WEIGHTS_PATH is set but file does not exist: %s", model_path)
            else:
                logger.info("Model weights found at %s", model_path)
        except Exception as exc:
            logger.exception("Error when checking model weights path: %s", exc)

    # Storage dir check (if using local storage)
    media_dir = os.getenv("MEDIA_DIR", "media")
    try:
        os.makedirs(media_dir, exist_ok=True)
        logger.info("Media directory available: %s", media_dir)
    except Exception as exc:
        logger.exception("Failed to ensure media dir %s: %s", media_dir, exc)
