import asyncio
import json

import httpx
import pytest

from app.config import Settings
from app.platforms import (
    BlueskyPlatform,
    DiscordPlatform,
    MastodonPlatform,
    RedditPlatform,
    TelegramPlatform,
)
from app.platforms.base import PostingError


def configured_settings() -> Settings:
    return Settings(
        mastodon_api_base_url="https://mastodon.example",
        mastodon_access_token="mastodon-token",
        bluesky_api_base_url="https://bsky.example",
        bluesky_identifier="account.example",
        bluesky_app_password="app-password",
        reddit_client_id="reddit-id",
        reddit_client_secret="reddit-secret",
        reddit_username="reddit-user",
        reddit_password="reddit-password",
        reddit_subreddit="test",
        telegram_bot_token="telegram-token",
        telegram_channel_username="public_channel",
        discord_webhook_url="https://discord.example/webhook",
        discord_guild_id="guild-id",
        discord_channel_id="channel-id",
    )


def test_mastodon_publishes_public_status():
    def handle(request):
        assert request.url.path == "/api/v1/statuses"
        assert request.headers["authorization"] == "Bearer mastodon-token"
        assert b"visibility=public" in request.content
        return httpx.Response(
            200,
            json={
                "url": "https://mastodon.example/@account/123",
                "created_at": "2026-01-02T03:04:05Z",
            },
        )

    receipt = asyncio.run(
        _post_with_mock(MastodonPlatform(configured_settings()), handle)
    )
    assert receipt.posted_url == "https://mastodon.example/@account/123"
    assert receipt.public_access is True


def test_bluesky_creates_session_and_public_post():
    calls = []

    def handle(request):
        calls.append(request.url.path)
        if request.url.path.endswith("createSession"):
            return httpx.Response(
                200, json={"accessJwt": "access-token", "did": "did:plc:account"}
            )
        assert request.headers["authorization"] == "Bearer access-token"
        assert (
            json.loads(request.content)["record"]["text"]
            == "Try this https://example.com"
        )
        return httpx.Response(
            200,
            json={"uri": "at://did:plc:account/app.bsky.feed.post/post-key"},
        )

    receipt = asyncio.run(
        _post_with_mock(BlueskyPlatform(configured_settings()), handle)
    )
    assert calls == [
        "/xrpc/com.atproto.server.createSession",
        "/xrpc/com.atproto.repo.createRecord",
    ]
    assert receipt.posted_url == "https://bsky.app/profile/did:plc:account/post/post-key"
    assert receipt.public_access is True


def test_reddit_submits_self_post():
    def handle(request):
        if request.url.path.endswith("/access_token"):
            return httpx.Response(200, json={"access_token": "reddit-access"})
        assert request.headers["authorization"] == "Bearer reddit-access"
        form = request.content.decode()
        assert "kind=self" in form
        assert "sr=test" in form
        return httpx.Response(
            200,
            json={
                "json": {
                    "errors": [],
                    "data": {"url": "https://www.reddit.com/r/test/comments/123/"},
                }
            },
        )

    receipt = asyncio.run(
        _post_with_mock(RedditPlatform(configured_settings()), handle)
    )
    assert receipt.posted_url == "https://www.reddit.com/r/test/comments/123/"
    assert receipt.public_access is True


def test_telegram_sends_to_configured_public_channel():
    def handle(request):
        assert request.url.path.endswith("/sendMessage")
        payload = json.loads(request.content)
        assert payload["chat_id"] == "@public_channel"
        assert payload["text"] == "Try this https://example.com"
        return httpx.Response(
            200, json={"ok": True, "result": {"message_id": 42}}
        )

    receipt = asyncio.run(
        _post_with_mock(TelegramPlatform(configured_settings()), handle)
    )
    assert receipt.posted_url == "https://t.me/public_channel/42"
    assert receipt.public_access is True


def test_telegram_error_includes_api_reason_without_bot_token():
    settings = configured_settings()

    def handle(request):
        return httpx.Response(
            400,
            json={
                "ok": False,
                "error_code": 400,
                "description": "Bad Request: chat not found",
            },
        )

    with pytest.raises(PostingError, match="Bad Request: chat not found"):
        asyncio.run(_post_with_mock(TelegramPlatform(settings), handle))


def test_discord_waits_for_message_and_returns_permalink():
    def handle(request):
        assert request.url.params["wait"] == "true"
        payload = json.loads(request.content)
        assert payload["content"] == "Try this https://example.com"
        assert payload["allowed_mentions"]["parse"] == []
        return httpx.Response(
            200,
            json={"id": "message-id", "channel_id": "channel-id", "guild_id": "guild-id"},
        )

    receipt = asyncio.run(
        _post_with_mock(DiscordPlatform(configured_settings()), handle)
    )
    assert (
        receipt.posted_url
        == "https://discord.com/channels/guild-id/channel-id/message-id"
    )
    assert receipt.public_access is False


async def _post_with_mock(platform, handler):
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        return await platform.post(client, "Try this https://example.com")
