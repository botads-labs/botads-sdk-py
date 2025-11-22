from typing import Any, Optional


class BotadsError(Exception):
    """Base error for SDK."""


class ApiError(BotadsError):
    def __init__(self, status_code: int, code: str, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details

    def __str__(self) -> str:
        return f"{self.status_code} {self.code}: {self.message}"
