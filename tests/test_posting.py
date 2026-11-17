import asyncio
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.platforms.base import PostReceipt, PostingError, PostingPlatform
from app.services.posting_service import post_message

client = TestClient(app)


class SuccessfulPlatform(PostingPlatform):
    name = "Success"

    async def post(self, client, message):
        return PostReceipt(
            posted_url="https://social.example/posts/123",
            public_access=True,
            posted_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc),
        )


class FailingPlatform(PostingPlatform):
    name = "Failure"

    async def post(self, client, message):
        raise PostingError("Rejected by test platform.")


def test_rejects_messages_over_200_characters():
    response = client.post(
        "/posting",
        json={"message": f"{'x' * 181} https://example.com"},
    )
    assert response.status_code == 422


def test_requires_exactly_one_valid_http_url():
    no_url = client.post("/posting", json={"message": "A message without a link"})
    two_urls = client.post(
        "/posting",
        json={"message": "https://one.example https://two.example"},
    )
    invalid_url = client.post(
        "/posting",
        json={"message": "Check https://?bad"},
    )
    assert no_url.status_code == 422
    assert two_urls.status_code == 422
    assert invalid_url.status_code == 422


def test_platform_failure_does_not_stop_other_platforms():
    response = asyncio.run(
        post_message(
            "Check this https://example.com",
            platforms=[FailingPlatform(), SuccessfulPlatform()],
        )
    )
    assert response.success is True
    assert [result.status for result in response.results] == ["failed", "success"]
    assert response.results[1].posted_url == "https://social.example/posts/123"
    assert response.results[1].date == "2026-01-02"
    assert response.results[1].time == "03:04:05"
