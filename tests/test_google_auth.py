from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

from app.main import app
from app.core.database import Base, get_db
from app.core.security import create_access_token, decrypt_sensitive_token
from app.infrastructure.db.models import UserTable, GoogleCredentialTable

# In-Memory SQLite Test Engine
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app, raise_server_exceptions=False)


def setup_module():
    """Initializes in-memory database schema for tests."""
    import asyncio
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    asyncio.run(init_models())


def test_google_oauth_url_generation():
    with patch("app.core.config.settings.GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com"):
        response = client.get("/api/v1/auth/google?state=xyz123")
        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "accounts.google.com" in data["authorization_url"]
        assert "gmail.readonly" in data["authorization_url"]


def test_google_oauth_user_denied_consent():
    response = client.get("/api/v1/auth/google/callback?error=access_denied")
    assert response.status_code == 400
    data = response.json()
    assert "User denied Google OAuth consent" in data["detail"]


def test_google_oauth_callback_successful_user_creation_and_token_security():
    mock_tokens = {
        "access_token": "ya29.mock_access_token_12345",
        "refresh_token": "1//mock_refresh_token_67890",
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=3600),
        "scopes": "https://www.googleapis.com/auth/gmail.readonly",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client-id"
    }

    mock_profile = {
        "google_id": "google-uid-1001",
        "email": "testuser@gmail.com",
        "full_name": "Test User",
        "picture": "https://lh3.googleusercontent.com/avatar.jpg"
    }

    with patch("app.infrastructure.google.oauth_service.GoogleOAuthService.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange, \
         patch("app.infrastructure.google.oauth_service.GoogleOAuthService.get_google_user_profile", new_callable=AsyncMock) as mock_get_profile:

        mock_exchange.return_value = mock_tokens
        mock_get_profile.return_value = mock_profile

        response = client.get("/api/v1/auth/google/callback?code=valid_test_auth_code")
        assert response.status_code == 200
        data = response.json()

        # Token Security Check: Ensure raw Google access/refresh tokens are NOT present in API response
        assert "ya29.mock_access_token_12345" not in str(data)
        assert "1//mock_refresh_token_67890" not in str(data)
        assert "access_token" in data  # CareerFlow JWT token
        assert data["user"]["email"] == "testuser@gmail.com"
        assert data["user"]["gmail_connected"] is True


def test_google_oauth_callback_repeated_login_prevents_duplicate_user():
    mock_tokens = {
        "access_token": "ya29.mock_access_token_repeat",
        "refresh_token": "1//mock_refresh_token_repeat",
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=3600),
        "scopes": "https://www.googleapis.com/auth/gmail.readonly",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test-client-id"
    }

    mock_profile = {
        "google_id": "google-uid-1001",
        "email": "testuser@gmail.com",
        "full_name": "Test User Updated",
        "picture": "https://lh3.googleusercontent.com/avatar.jpg"
    }

    with patch("app.infrastructure.google.oauth_service.GoogleOAuthService.exchange_code_for_tokens", new_callable=AsyncMock) as mock_exchange, \
         patch("app.infrastructure.google.oauth_service.GoogleOAuthService.get_google_user_profile", new_callable=AsyncMock) as mock_get_profile:

        mock_exchange.return_value = mock_tokens
        mock_get_profile.return_value = mock_profile

        response = client.get("/api/v1/auth/google/callback?code=another_valid_code")
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["full_name"] == "Test User Updated"


def test_gmail_status_and_disconnect_flow():
    import asyncio
    async def get_test_user_id():
        async with TestingSessionLocal() as session:
            res = await session.execute(select(UserTable).where(UserTable.email == "testuser@gmail.com"))
            user = res.scalar_one()
            return str(user.id)

    user_id_str = asyncio.run(get_test_user_id())
    jwt_token = create_access_token(user_id_str)
    headers = {"Authorization": f"Bearer {jwt_token}"}

    # 1. Test GET /api/v1/gmail/status
    status_resp = client.get("/api/v1/gmail/status", headers=headers)
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["connected"] is True
    assert status_data["email"] == "testuser@gmail.com"
    # Ensure raw OAuth tokens are NOT returned in status endpoint
    assert "access_token" not in status_data

    # 2. Test POST /api/v1/gmail/disconnect
    disconnect_resp = client.post("/api/v1/gmail/disconnect", headers=headers)
    assert disconnect_resp.status_code == 200
    disconnect_data = disconnect_resp.json()
    assert disconnect_data["connected"] is False

    # 3. Verify status after disconnect
    status_after = client.get("/api/v1/gmail/status", headers=headers)
    assert status_after.status_code == 200
    assert status_after.json()["connected"] is False
