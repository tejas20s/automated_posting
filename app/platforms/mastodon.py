from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.config import Settings
from app.platforms.base import (
    PostReceipt,
    PostingError,
    PostingPlatform,
    parsed_timestamp,
    require_configured,
    require_success,
    required_string,
    response_json,
)


class MastodonPlatform(PostingPlatform):
    name = "Mastodon"

    def __init__(self, settings: Settings) -> None:
        self.api_base_url = settings.mastodon_api_base_url
        self.access_token = settings.mastodon_access_token

    async def post(self, client: httpx.AsyncClient, message: str) -> PostReceipt:
        require_configured(access_token=self.access_token)
        response = await client.post(
            f"{self.api_base_url}/api/v1/statuses",
            data={"status": message, "visibility": "public"},
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Idempotency-Key": str(uuid4()),
            },
        )
        require_success(response)
        data = response_json(response)
        posted_url = required_string(data, "url")
        return PostReceipt(
            posted_url=posted_url,
            public_access=True,
            posted_at=parsed_timestamp(data.get("created_at")) or datetime.now(timezone.utc),
        )
