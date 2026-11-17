from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.platforms.base import (
    PostReceipt,
    PostingError,
    PostingPlatform,
    require_configured,
    response_json,
)


class TelegramPlatform(PostingPlatform):
    name = "Telegram"

    def __init__(self, settings: Settings) -> None:
        self.bot_token = settings.telegram_bot_token
        self.channel_username = settings.telegram_channel_username

    async def post(self, client: httpx.AsyncClient, message: str) -> PostReceipt:
        require_configured(
            bot_token=self.bot_token,
            channel_username=self.channel_username,
        )
        username = (self.channel_username or "").removeprefix("@")
        if not username:
            raise PostingError("Telegram public channel username is invalid.")

        response = await client.post(
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
            json={"chat_id": f"@{username}", "text": message},
        )
        data = response_json(response)
        if not response.is_success:
            description = data.get("description")
            if isinstance(description, str) and description:
                safe_description = description.replace(self.bot_token or "", "[redacted]")
                raise PostingError(
                    f"Telegram API returned HTTP {response.status_code}: "
                    f"{safe_description}"
                )
            raise PostingError(f"Telegram API returned HTTP {response.status_code}.")
        if data.get("ok") is not True:
            description = data.get("description")
            if isinstance(description, str) and description:
                safe_description = description.replace(self.bot_token or "", "[redacted]")
                raise PostingError(f"Telegram rejected the message: {safe_description}")
            raise PostingError("Telegram rejected the message.")
        result = data.get("result")
        if not isinstance(result, dict):
            raise PostingError("Telegram returned an unexpected message response.")
        message_id = result.get("message_id")
        if not isinstance(message_id, (int, str)) or not str(message_id):
            raise PostingError("Telegram response was missing the message identifier.")

        return PostReceipt(
            posted_url=f"https://t.me/{username}/{message_id}",
            public_access=True,
            posted_at=datetime.now(timezone.utc),
        )
