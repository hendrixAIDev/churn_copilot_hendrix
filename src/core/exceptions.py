"""Custom exceptions for ChurnPilot."""


class ChurnPilotError(Exception):
    """Base exception for all ChurnPilot errors."""

    pass


class ExtractionError(ChurnPilotError):
    """Raised when AI extraction fails."""

    pass


class StorageError(ChurnPilotError):
    """Raised when data persistence fails."""

    pass


class ValidationError(ChurnPilotError):
    """Raised when data validation fails."""

    pass


class FetchError(ChurnPilotError):
    """Raised when URL fetching fails."""

    pass
