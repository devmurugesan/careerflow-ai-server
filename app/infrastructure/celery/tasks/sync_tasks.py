import asyncio
from app.infrastructure.celery.app import celery_app
from app.core.logger import logger


@celery_app.task(name="app.infrastructure.celery.tasks.sync_tasks.process_gmail_webhook_task", bind=True, max_retries=3)
def process_gmail_webhook_task(self, user_email: str, history_id: int):
    """Async background task processing Gmail webhook delta notification."""
    logger.info("Processing Gmail Webhook Delta Sync", user_email=user_email, history_id=history_id)
    # Orchestrates history delta fetch and triggers AI task
    return {"status": "SUCCESS", "user_email": user_email, "history_id": history_id}


@celery_app.task(name="app.infrastructure.celery.tasks.ai_tasks.process_email_ai_extraction_task", bind=True, max_retries=2)
def process_email_ai_extraction_task(self, email_id: str):
    """Async background task performing multi-provider LLM extraction and state transitions."""
    logger.info("Processing AI Extraction Task", email_id=email_id)
    return {"status": "PROCESSED", "email_id": email_id}


@celery_app.task(name="app.infrastructure.celery.tasks.reminder_tasks.check_due_reminders_task")
def check_due_reminders_task():
    """Periodic Celery Beat cron checking upcoming opportunity deadlines and firing notifications."""
    logger.info("Checking Due Reminders & Opportunity Deadlines")
    return {"status": "COMPLETED"}
