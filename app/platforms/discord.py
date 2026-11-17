from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.platforms.base import (
    PostReceipt,
    PostingPlatform,
    require_configured,
    require_success,
    response_json,
)


class DiscordPlatform(PostingPlatform):
    name = "Discord"

    def __init__(self, settings: Settings) -> None:
        self.webhook_url = settings.discord_webhook_url
        self.guild_id = settings.discord_guild_id
        self.channel_id = settings.discord_channel_id

    async def post(self, client: httpx.AsyncClient, message: str) -> PostReceipt:
        require_configured(webhook_url=self.webhook_url)
        response = await client.post(
            self.webhook_url or "",
            params={"wait": "true"},
            json={"content": message, "allowed_mentions": {"parse": []}},
        )
        require_success(response)
        data = response_json(response)
        message_id = data.get("id")
        channel_id = data.get("channel_id") or self.channel_id
        guild_id = data.get("guild_id") or self.guild_id
        posted_url = None
        if (
            isinstance(message_id, (int, str))
            and str(message_id)
            and isinstance(channel_id, (int, str))
            and str(channel_id)
            and isinstance(guild_id, (int, str))
            and str(guild_id)
        ):
            posted_url = (
                f"https://discord.com/channels/{guild_id}/{channel_id}/{message_id}"
            )

        return PostReceipt(
            posted_url=posted_url,
            public_access=False,
            posted_at=datetime.now(timezone.utc),
        )
