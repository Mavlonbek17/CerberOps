"""Celery application configuration."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "cerberops",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Reliability
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,

    # Time limits
    task_soft_time_limit=2400,   # 40 minutes soft
    task_hard_time_limit=2700,   # 45 minutes hard

    # Result expiry
    result_expires=86400,  # 24 hours

    # Task routing
    task_routes={
        "app.tasks.scan_tasks.*": {"queue": "scans"},
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
