from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "careerflow_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.infrastructure.celery.tasks.sync_tasks.*": {"queue": "gmail_sync"},
        "app.infrastructure.celery.tasks.ai_tasks.*": {"queue": "ai_processing"},
        "app.infrastructure.celery.tasks.reminder_tasks.*": {"queue": "reminders"},
    },
    beat_schedule={
        "check-upcoming-reminders": {
            "task": "app.infrastructure.celery.tasks.reminder_tasks.check_due_reminders_task",
            "schedule": 60.0, # Every 60 seconds
        },
    }
)
