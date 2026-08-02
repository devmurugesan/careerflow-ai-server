from app.core.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.PROJECT_NAME == "CareerFlow AI"
    assert settings.API_V1_STR == "/api/v1"
    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert "postgresql://" in settings.SYNC_DATABASE_URL


def test_cors_origins_parsing():
    settings = Settings(CORS_ORIGINS='["http://localhost:3000","http://example.com"]')
    assert len(settings.CORS_ORIGINS) == 2
    assert "http://localhost:3000" in settings.CORS_ORIGINS
    assert "http://example.com" in settings.CORS_ORIGINS
