import os

from celery import Celery
from dotenv import load_dotenv

# Import logging configuration
import app.logging_config

load_dotenv()

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "docuverse_worker",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.tasks"],  # You will define tasks in app/tasks.py
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Logging configuration
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    worker_log_color=True,
    # Task routing
    task_routes={
        "app.tasks.process_document_task": {"queue": "docuverse"},
    },
    # Task annotations for monitoring
    task_annotations={
        "app.tasks.process_document_task": {
            "rate_limit": "10/m",
            "time_limit": 1800,  # 30 minutes
            "soft_time_limit": 1500,  # 25 minutes
        }
    },
)
