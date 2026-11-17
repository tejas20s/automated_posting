from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import httpx


class PostingError(Exception):
    """A safe, user-facing platform posting error."""


@dataclass(frozen=True)
class PostReceipt:
    posted_url: str | None
    public_access: bool
    posted_at: datetime


class PostingPlatform(ABC):
    name: str

    @abstractmethod
    async def post(self, client: httpx.AsyncClient, message: str) -> PostReceipt:
        raise NotImplementedError


def require_configured(**values: str | None) -> None:
    if any(not value for value in values.values()):
        raise PostingError("Platform credentials or target are not configured.")


def require_success(response: httpx.Response) -> None:
    if not response.is_success:
        raise PostingError(f"Platform API returned HTTP {response.status_code}.")


def response_json(response: httpx.Response) -> dict:
    try:
        data = response.json()
    except (ValueError, UnicodeDecodeError) as exc:
        raise PostingError("Platform API returned an invalid JSON response.") from exc
    if not isinstance(data, dict):
        raise PostingError("Platform API returned an unexpected response.")
    return data


def required_string(data: dict, key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise PostingError("Platform API response was missing required post data.")
    return value


def parsed_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
