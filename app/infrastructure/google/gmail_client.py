import base64
from typing import List, Dict, Any, Optional
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from app.core.config import settings


class GmailClient:
    """Gmail REST API client wrapper for fetching email delta updates."""

    def __init__(self, access_token: str, refresh_token: str):
        self.credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET
        )
        self.service = build("gmail", "v1", credentials=self.credentials)

    def fetch_history_delta(self, start_history_id: int) -> List[str]:
        """Fetches added email message IDs since the last history_id checkpoint."""
        try:
            response = self.service.users().history().list(
                userId="me",
                startHistoryId=start_history_id,
                historyTypes=["messageAdded"]
            ).execute()
            
            message_ids = []
            histories = response.get("history", [])
            for history in histories:
                messages_added = history.get("messagesAdded", [])
                for msg in messages_added:
                    message_ids.append(msg["message"]["id"])
            return list(set(message_ids))
        except Exception:
            return []

    def get_message_detail(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves raw full details of a specific message ID."""
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            headers = {h["name"].lower(): h["value"] for h in message["payload"]["headers"]}
            subject = headers.get("subject", "No Subject")
            sender = headers.get("from", "Unknown")
            recipient = headers.get("to", "")
            received_at = headers.get("date", "")

            body = ""
            payload = message["payload"]
            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain" and "data" in part["body"]:
                        body += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
            elif "body" in payload and "data" in payload["body"]:
                body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

            return {
                "gmail_message_id": message_id,
                "thread_id": message.get("threadId"),
                "snippet": message.get("snippet", ""),
                "subject": subject,
                "sender": sender,
                "recipient": recipient,
                "body": body,
                "history_id": int(message.get("historyId", 0))
            }
        except Exception:
            return None
