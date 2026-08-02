from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logger import logger


class DomainException(Exception):
    """Base domain logic exception."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(DomainException):
    """Raised when requested domain entity is missing."""
    pass


class InvalidStateTransitionException(DomainException):
    """Raised when an invalid state transition is attempted."""
    pass


class DatabaseConnectionException(DomainException):
    """Raised when database operations fail or disconnect."""
    pass


class AuthenticationException(DomainException):
    """Raised on invalid credentials or token expiration."""
    pass


async def domain_exception_handler(request: Request, exc: DomainException):
    """Handler converting domain exceptions to clean JSON error responses."""
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, EntityNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, AuthenticationException):
        status_code = status.HTTP_401_UNAUTHORIZED
    elif isinstance(exc, InvalidStateTransitionException):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY

    logger.warning("Domain exception occurred", error_type=exc.__class__.__name__, detail=exc.message)

    return JSONResponse(
        status_code=status_code,
        content={"error": exc.__class__.__name__, "detail": exc.message}
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Global fallback exception handler to catch unhandled exceptions without leaking stack traces."""
    logger.error("Unhandled server exception", error=str(exc), path=request.url.path)
    
    # Hide internal stack traces in production responses
    detail_msg = str(exc) if settings.DEBUG else "Internal Server Error"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "InternalServerError", "detail": detail_msg}
    )
