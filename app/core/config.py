import json
from typing import List, Union, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = Field(default="CareerFlow AI")
    VERSION: str = Field(default="1.0.0")
    API_V1_STR: str = Field(default="/api/v1")
    
    # Environment
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = Field(
        default=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:3000"]
    )
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return ["http://localhost:3000"]

    # Security
    SECRET_KEY: str = Field(default="super_secret_jwt_key_change_in_production_32_bytes_min")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=1440)  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=30)
    ENCRYPTION_KEY: str = Field(default="g0W-d-M4t9sP_8QyK7Z1vX3bN6mC5vB4aS3dF2gH1jK=")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = Field(default="your-google-client-id.apps.googleusercontent.com")
    GOOGLE_CLIENT_SECRET: str = Field(default="your-google-client-secret")
    GOOGLE_REDIRECT_URI: str = Field(default="http://localhost:8000/api/v1/auth/google/callback")
    
    # PostgreSQL Database
    POSTGRES_USER: str = Field(default="careerflow")
    POSTGRES_PASSWORD: str = Field(default="careerflow_pass")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="careerflow_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Redis & Celery
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
