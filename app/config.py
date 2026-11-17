import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    mastodon_api_base_url: str
    mastodon_access_token: str | None
    bluesky_api_base_url: str
    bluesky_identifier: str | None
    bluesky_app_password: str | None
    reddit_client_id: str | None
    reddit_client_secret: str | None
    reddit_username: str | None
    reddit_password: str | None
    reddit_subreddit: str | None
    telegram_bot_token: str | None
    telegram_channel_username: str | None
    discord_webhook_url: str | None
    discord_guild_id: str | None
    discord_channel_id: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            mastodon_api_base_url=os.getenv(
                "MASTODON_API_BASE_URL", "https://mastodon.social"
            ).rstrip("/"),
            mastodon_access_token=os.getenv("MASTODON_ACCESS_TOKEN"),
            bluesky_api_base_url=os.getenv(
                "BLUESKY_API_BASE_URL", "https://bsky.social"
            ).rstrip("/"),
            bluesky_identifier=os.getenv("BLUESKY_IDENTIFIER"),
            bluesky_app_password=os.getenv("BLUESKY_APP_PASSWORD"),
            reddit_client_id=os.getenv("REDDIT_CLIENT_ID"),
            reddit_client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            reddit_username=os.getenv("REDDIT_USERNAME"),
            reddit_password=os.getenv("REDDIT_PASSWORD"),
            reddit_subreddit=os.getenv("REDDIT_SUBREDDIT"),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
            telegram_channel_username=os.getenv("TELEGRAM_CHANNEL_USERNAME"),
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL"),
            discord_guild_id=os.getenv("DISCORD_GUILD_ID"),
            discord_channel_id=os.getenv("DISCORD_CHANNEL_ID"),
        )
