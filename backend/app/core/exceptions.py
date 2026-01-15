"""Custom application exceptions."""

from typing import Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        code: str = "UNKNOWN_ERROR",
        details: Optional[dict] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API response."""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


class EntityNotFoundError(AppException):
    """Raised when an entity is not found."""

    def __init__(self, entity_type: str, entity_id: int):
        super().__init__(
            message=f"{entity_type} with id {entity_id} not found",
            code="ENTITY_NOT_FOUND",
            details={"entity_type": entity_type, "entity_id": entity_id},
        )
        self.entity_type = entity_type
        self.entity_id = entity_id


class OptimizationFailedError(AppException):
    """Raised when menu optimization fails."""

    def __init__(self, reason: str, solver_status: Optional[str] = None):
        super().__init__(
            message=f"Optimization failed: {reason}",
            code="OPTIMIZATION_FAILED",
            details={"reason": reason, "solver_status": solver_status},
        )
        self.reason = reason
        self.solver_status = solver_status


class ExternalServiceError(AppException):
    """Raised when an external service call fails."""

    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"{service} error: {reason}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "reason": reason},
        )
        self.service = service
        self.reason = reason


class ValidationError(AppException):
    """Raised when validation fails."""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validation error on {field}: {reason}",
            code="VALIDATION_ERROR",
            details={"field": field, "reason": reason},
        )
        self.field = field
        self.reason = reason


class DuplicateEntityError(AppException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity_type: str, identifier: str):
        super().__init__(
            message=f"{entity_type} '{identifier}' already exists",
            code="DUPLICATE_ENTITY",
            details={"entity_type": entity_type, "identifier": identifier},
        )


class InsufficientDataError(AppException):
    """Raised when there is insufficient data for an operation."""

    def __init__(self, reason: str):
        super().__init__(
            message=f"Insufficient data: {reason}",
            code="INSUFFICIENT_DATA",
            details={"reason": reason},
        )
