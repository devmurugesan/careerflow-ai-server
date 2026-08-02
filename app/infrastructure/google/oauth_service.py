from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
import httpx
from google_auth_oauthlib.flow import Flow
from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import AuthenticationException

GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    GMAIL_READONLY_SCOPE
]


class GoogleOAuthService:
    """Service handling Google OAuth 2.0 flow, token exchange, and profile retrieval."""

    @staticmethod
    def get_authorization_url(state: Optional[str] = None) -> str:
        """Generates Google OAuth 2.0 URL requesting offline access for refresh tokens."""
        if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "your-google-client-id":
            raise AuthenticationException("Google Client ID is not configured in settings")

        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            state=state
        )
        return auth_url

    @staticmethod
    async def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        """Exchanges authorization code for access and refresh tokens via Google token endpoint."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error("Failed Google token exchange", status=response.status_code)
                raise AuthenticationException("Invalid or expired Google authorization code")

            data = response.json()
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            return {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token", ""),
                "expires_at": expires_at,
                "scopes": data.get("scope", ",".join(SCOPES)),
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": settings.GOOGLE_CLIENT_ID
            }

    @staticmethod
    async def get_google_user_profile(access_token: str) -> Dict[str, Any]:
        """Fetches standard user email and profile details from Google UserInfo API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )

            if response.status_code != 200:
                logger.error("Failed fetching Google UserInfo profile", status=response.status_code)
                raise AuthenticationException("Failed to retrieve Google user profile")

            data = response.json()
            return {
                "google_id": data.get("id"),
                "email": data.get("email"),
                "full_name": data.get("name") or data.get("email", "").split("@")[0],
                "picture": data.get("picture")
            }
