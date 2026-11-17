from datetime import datetime, timezone

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


class BlueskyPlatform(PostingPlatform):
    name = "Bluesky"

    def __init__(self, settings: Settings) -> None:
        self.api_base_url = settings.bluesky_api_base_url
        self.identifier = settings.bluesky_identifier
        self.app_password = settings.bluesky_app_password

    async def post(self, client: httpx.AsyncClient, message: str) -> PostReceipt:
        require_configured(
            identifier=self.identifier,
            app_password=self.app_password,
        )
        session_response = await client.post(
            f"{self.api_base_url}/xrpc/com.atproto.server.createSession",
            json={
                "identifier": self.identifier,
                "password": self.app_password,
            },
        )
        require_success(session_response)
        session = response_json(session_response)
        access_token = required_string(session, "accessJwt")
        did = required_string(session, "did")

        created_at = datetime.now(timezone.utc)
        record_response = await client.post(
            f"{self.api_base_url}/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "repo": did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": message,
                    "createdAt": created_at.isoformat().replace("+00:00", "Z"),
                },
            },
        )
        require_success(record_response)
        record = response_json(record_response)
        uri = required_string(record, "uri")
        rkey = uri.rsplit("/", 1)[-1]
        if not rkey:
            raise PostingError("Bluesky returned an invalid post identifier.")

        return PostReceipt(
            posted_url=f"https://bsky.app/profile/{did}/post/{rkey}",
            public_access=True,
            posted_at=parsed_timestamp(record.get("createdAt")) or created_at,
        )
