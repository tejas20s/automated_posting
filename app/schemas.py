import re
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, field_validator


_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_URL_ADAPTER = TypeAdapter(HttpUrl)


def _trim_url_punctuation(candidate: str) -> str:
    candidate = candidate.rstrip(".,!?;:")
    for closing, opening in ((")", "("), ("]", "["), ("}", "{")):
        while candidate.endswith(closing) and candidate.count(closing) > candidate.count(
            opening
        ):
            candidate = candidate[:-1]
    return candidate


class PostingRequest(BaseModel):
    message: str = Field(min_length=1, max_length=200)

    @field_validator("message")
    @classmethod
    def require_one_valid_link(cls, message: str) -> str:
        matches = _URL_PATTERN.findall(message)
        if len(matches) != 1:
            raise ValueError("Message must contain exactly one CTA link.")

        url = _trim_url_punctuation(matches[0])
        try:
            _URL_ADAPTER.validate_python(url)
        except ValueError as exc:
            raise ValueError("CTA link must be a valid HTTP or HTTPS URL.") from exc
        return message


class PlatformResult(BaseModel):
    platform: str
    status: Literal["success", "failed"]
    posted_url: str | None
    published_content: str | None
    public_access: bool
    date: str | None
    time: str | None
    error: str | None


class PostingResponse(BaseModel):
    success: bool
    results: list[PlatformResult]
