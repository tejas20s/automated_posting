import asyncio
from datetime import datetime, timezone
from typing import Sequence

import httpx

from app.config import Settings
from app.platforms import (
    BlueskyPlatform,
    DiscordPlatform,
    MastodonPlatform,
    RedditPlatform,
    TelegramPlatform,
)
from app.platforms.base import PostReceipt, PostingError, PostingPlatform
from app.schemas import PlatformResult, PostingResponse


def create_platforms(settings: Settings) -> list[PostingPlatform]:
    return [
        MastodonPlatform(settings),
        BlueskyPlatform(settings),
        RedditPlatform(settings),
        TelegramPlatform(settings),
        DiscordPlatform(settings),
    ]


def _success_result(
    platform: PostingPlatform, message: str, receipt: PostReceipt
) -> PlatformResult:
    posted_at = receipt.posted_at
    if posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)
    posted_at = posted_at.astimezone(timezone.utc)
    return PlatformResult(
        platform=platform.name,
        status="success",
        posted_url=receipt.posted_url,
        published_content=message,
        public_access=receipt.public_access,
        date=posted_at.date().isoformat(),
        time=posted_at.time().replace(microsecond=0).isoformat(),
        error=None,
    )


def _failure_result(platform: PostingPlatform, message: str) -> PlatformResult:
    return PlatformResult(
        platform=platform.name,
        status="failed",
        posted_url=None,
        published_content=None,
        public_access=False,
        date=None,
        time=None,
        error=message,
    )


async def _post_one(
    client: httpx.AsyncClient, platform: PostingPlatform, message: str
) -> PlatformResult:
    try:
        receipt = await platform.post(client, message)
    except PostingError as exc:
        return _failure_result(platform, str(exc))
    except (httpx.HTTPError, httpx.InvalidURL):
        return _failure_result(platform, "Could not communicate with the platform API.")
    return _success_result(platform, message, receipt)


async def post_message(
    message: str,
    settings: Settings | None = None,
    platforms: Sequence[PostingPlatform] | None = None,
) -> PostingResponse:
    selected_settings = settings or Settings.from_env()
    selected_platforms = platforms or create_platforms(selected_settings)
    async with httpx.AsyncClient(timeout=20.0) as client:
        results = await asyncio.gather(
            *(
                _post_one(client, platform, message)
                for platform in selected_platforms
            )
        )
    return PostingResponse(
        success=any(result.status == "success" for result in results),
        results=results,
    )
