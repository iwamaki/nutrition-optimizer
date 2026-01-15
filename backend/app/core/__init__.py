"""Core module - Application shared configuration and utilities."""

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    EntityNotFoundError,
    OptimizationFailedError,
    ExternalServiceError,
    ValidationError,
)

__all__ = [
    "settings",
    "AppException",
    "EntityNotFoundError",
    "OptimizationFailedError",
    "ExternalServiceError",
    "ValidationError",
]
