from dataclasses import dataclass
from typing import Optional

import requests

from .errors import ApiError
from .constants import DEFAULT_API_BASE_URL, DEFAULT_DIRECT_LINK_BASE_URL


@dataclass
class CodeResponse:
    code: str
    expires_in: int
    expires_at: str

    def direct_link_url(self, base_url: str = DEFAULT_DIRECT_LINK_BASE_URL) -> str:
        return f"{base_url.rstrip('/')}/{self.code}"

    @property
    def direct_link(self) -> str:
        return self.direct_link_url()


class BotadsClient:
    """Synchronous client for the Botads Client API."""

    def __init__(
        self,
        base_url: str = DEFAULT_API_BASE_URL,
        api_token: str = "",
        timeout: float = 10.0,
    ):
        if not api_token:
            raise ValueError("api_token is required")
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            }
        )

    def create_code(self, bot_id: int, user_tg_id: str) -> CodeResponse:
        """Request a new short code."""
        payload = {"bot_id": str(bot_id), "user_tg_id": user_tg_id}
        url = f"{self.base_url}/client/v1/codes"
        response = self._session.post(url, json=payload, timeout=self.timeout)
        if response.status_code != 200:
            raise _parse_api_error(response)
        data = response.json()
        return CodeResponse(
            code=data["code"],
            expires_in=int(data["expires_in"]),
            expires_at=data["expires_at"],
        )

    def close(self) -> None:
        self._session.close()


def _parse_api_error(response: requests.Response) -> ApiError:
    try:
        payload = response.json()
    except Exception:
        return ApiError(response.status_code, "UNKNOWN", response.text)
    err = payload.get("error", {})
    return ApiError(
        response.status_code,
        err.get("code", "UNKNOWN"),
        err.get("message", "Unknown error"),
        err.get("details"),
    )
