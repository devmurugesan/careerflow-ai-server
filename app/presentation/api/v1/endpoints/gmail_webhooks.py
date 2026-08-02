import base64
import json
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Body
from pydantic import BaseModel
from app.infrastructure.celery.tasks.sync_tasks import process_gmail_webhook_task
from app.core.logger import logger

router = APIRouter(prefix="/gmail", tags=["Gmail Webhooks & Integration"])


class PubSubMessage(BaseModel):
    data: str
    messageId: str
    publishTime: str


class PubSubPayload(BaseModel):
    message: PubSubMessage
    subscription: str


@router.post("/webhooks", status_code=status.HTTP_200_OK)
async def receive_gmail_pubsub_webhook(payload: PubSubPayload = Body(...)):
    """Webhook endpoint invoked by Google Cloud Pub/Sub when a user receives a new email."""
    try:
        decoded_bytes = base64.b64decode(payload.message.data)
        notification_data = json.loads(decoded_bytes.decode("utf-8"))

        user_email = notification_data.get("emailAddress")
        history_id = notification_data.get("historyId")

        if not user_email or not history_id:
            return {"status": "IGNORED", "reason": "Missing email or historyId"}

        # Enqueue async Celery task immediately to avoid holding HTTP connection open
        process_gmail_webhook_task.delay(user_email, int(history_id))

        return {"status": "QUEUED", "message_id": payload.message.messageId}
    except Exception as e:
        logger.error("Error processing Gmail PubSub Webhook", error=str(e))
        return {"status": "ERROR", "detail": str(e)}
