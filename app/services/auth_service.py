from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.security import (
    encrypt_sensitive_token,
    create_access_token,
    create_refresh_token
)
from app.core.exceptions import AuthenticationException
from app.core.logger import logger
from app.infrastructure.db.models import UserTable, GoogleCredentialTable
from app.infrastructure.google.oauth_service import GoogleOAuthService


class AuthService:
    """Service encapsulating authentication use cases and Google OAuth flows."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def authenticate_google_user(self, code: str) -> Dict[str, Any]:
        """Orchestrates code exchange, profile fetch, user upsert, AES-256 token storage, and JWT issue."""
        # 1. Exchange code for Google OAuth tokens
        tokens = await GoogleOAuthService.exchange_code_for_tokens(code)
        
        # 2. Retrieve user Google profile
        profile = await GoogleOAuthService.get_google_user_profile(tokens["access_token"])
        
        google_id = profile["google_id"]
        email = profile["email"]
        full_name = profile["full_name"]

        if not email:
            raise AuthenticationException("Google account did not return an email address")

        # 3. Find or Create User (No Duplicate Users)
        stmt = select(UserTable).where(
            or_(UserTable.email == email, UserTable.google_id == google_id)
        )
        res = await self.session.execute(stmt)
        user = res.scalar_one_or_none()

        if user:
            user.google_id = google_id
            user.full_name = full_name
            user.updated_at = datetime.now(timezone.utc)
        else:
            user = UserTable(
                email=email,
                google_id=google_id,
                full_name=full_name
            )
            self.session.add(user)
            await self.session.flush()

        # 4. Encrypt tokens before writing to database
        encrypted_access = encrypt_sensitive_token(tokens["access_token"])
        encrypted_refresh = encrypt_sensitive_token(tokens["refresh_token"]) if tokens.get("refresh_token") else ""

        # 5. UPSERT Google Credentials
        stmt_cred = select(GoogleCredentialTable).where(GoogleCredentialTable.user_id == user.id)
        res_cred = await self.session.execute(stmt_cred)
        cred = res_cred.scalar_one_or_none()

        if cred:
            cred.encrypted_access_token = encrypted_access
            if encrypted_refresh:
                cred.encrypted_refresh_token = encrypted_refresh
            cred.expires_at = tokens["expires_at"]
            cred.scopes = tokens["scopes"]
            cred.is_connected = True
            cred.updated_at = datetime.now(timezone.utc)
        else:
            cred = GoogleCredentialTable(
                user_id=user.id,
                encrypted_access_token=encrypted_access,
                encrypted_refresh_token=encrypted_refresh,
                token_uri=tokens["token_uri"],
                client_id=tokens["client_id"],
                scopes=tokens["scopes"],
                expires_at=tokens["expires_at"],
                is_connected=True
            )
            self.session.add(cred)

        await self.session.commit()
        await self.session.refresh(user)

        # 6. Issue JWT Tokens for CareerFlow API
        access_jwt = create_access_token(user.id)
        refresh_jwt = create_refresh_token(user.id)

        logger.info("Google OAuth authentication successful", user_id=str(user.id), email=user.email)

        return {
            "message": "Google Authentication successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "gmail_connected": True
            },
            "access_token": access_jwt,
            "refresh_token": refresh_jwt,
            "token_type": "bearer"
        }
