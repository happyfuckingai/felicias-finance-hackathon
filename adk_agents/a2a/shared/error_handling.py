"""
A2A Protocol Error Handling

This module defines custom exceptions and error handling utilities
for the A2A protocol.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class A2AError(Exception):
    """Base exception for all A2A protocol errors."""

    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "A2A_ERROR"
        self.details = details or {}
        self.timestamp = datetime.utcnow()
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format for transmission."""
        return {
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class ConnectionError(A2AError):
    """Exception raised when connection issues occur."""

    def __init__(self, message: str, target_agent: str = None, connection_type: str = "unknown"):
        details = {"target_agent": target_agent, "connection_type": connection_type}
        super().__init__(message, "CONNECTION_ERROR", details)


class ProtocolError(A2AError):
    """Exception raised when protocol violations occur."""

    def __init__(self, message: str, protocol_version: str = None, message_type: str = None):
        details = {"protocol_version": protocol_version, "message_type": message_type}
        super().__init__(message, "PROTOCOL_ERROR", details)


class AuthenticationError(A2AError):
    """Exception raised when authentication fails."""

    def __init__(self, message: str, agent_id: str = None, auth_method: str = "unknown"):
        details = {"agent_id": agent_id, "auth_method": auth_method}
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class ValidationError(A2AError):
    """Exception raised when message validation fails."""

    def __init__(self, message: str, field: str = None, expected_format: str = None):
        details = {"field": field, "expected_format": expected_format}
        super().__init__(message, "VALIDATION_ERROR", details)


class TimeoutError(A2AError):
    """Exception raised when operations timeout."""

    def __init__(self, message: str, timeout_seconds: int = None, operation: str = None):
        details = {"timeout_seconds": timeout_seconds, "operation": operation}
        super().__init__(message, "TIMEOUT_ERROR", details)


class ErrorHandler:
    """Utility class for handling and logging A2A errors."""

    @staticmethod
    def log_error(error: A2AError, agent_id: str = None):
        """Log an A2A error with appropriate context."""
        context = f"Agent {agent_id}: " if agent_id else ""
        logger.error(f"{context}{error.error_code}: {error.message}")

        if error.details:
            logger.debug(f"Error details: {error.details}")

    @staticmethod
    def create_error_response(error: A2AError, original_message_id: str = None) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            "error": True,
            "error_code": error.error_code,
            "message": error.message,
            "details": error.details,
            "timestamp": error.timestamp.isoformat(),
            "original_message_id": original_message_id
        }

    @staticmethod
    async def handle_async_error(coro_func, agent_id: str = None, fallback_value: Any = None):
        """Execute a coroutine with error handling."""
        try:
            return await coro_func
        except A2AError as e:
            ErrorHandler.log_error(e, agent_id)
            return fallback_value
        except Exception as e:
            # Wrap unexpected errors
            wrapped_error = A2AError(f"Unexpected error: {str(e)}", "UNEXPECTED_ERROR")
            ErrorHandler.log_error(wrapped_error, agent_id)
            return fallback_value