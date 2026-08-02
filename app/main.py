from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logger import setup_logging, logger
from app.core.exceptions import (
    DomainException,
    domain_exception_handler,
    global_exception_handler
)
from app.presentation.api.v1.router import api_v1_router
from app.presentation.api.v1.endpoints.health import health_check


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events lifecycle manager."""
    setup_logging()
    logger.info("Starting CareerFlow AI Backend Foundation", environment=settings.ENVIRONMENT, version=settings.VERSION)
    yield
    logger.info("Shutting down CareerFlow AI Backend Engine")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Security & CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(DomainException, domain_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Versioned API Routers
app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Top-level Health check endpoint for ALB / Kubernetes
app.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])
