from datetime import datetime, timedelta, timezone
from typing import Any, Union
import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
fernet = Fernet(settings.ENCRYPTION_KEY.encode() if len(settings.ENCRYPTION_KEY) == 44 else Fernet.generate_key())


def hash_password(password: str) -> str:
    """Hashes plain text password."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plain password against bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    """Creates a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """Creates a JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decodes JWT token and validates payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def encrypt_sensitive_token(token_str: str) -> str:
    """Encrypts OAuth tokens at rest using AES-256 Fernet."""
    if not token_str:
        return ""
    return fernet.encrypt(token_str.encode()).decode()


def decrypt_sensitive_token(encrypted_token: str) -> str:
    """Decrypts OAuth tokens from storage."""
    if not encrypted_token:
        return ""
    return fernet.decrypt(encrypted_token.encode()).decode()
