from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.platforms.base import (
    PostReceipt,
    PostingError,
    PostingPlatform,
    require_configured,
    require_success,
    response_json,
)


class RedditPlatform(PostingPlatform):
    name = "Reddit"

    def __init__(self, settings: Settings) -> None:
        self.client_id = settings.reddit_client_id
        self.client_secret = settings.reddit_client_secret
        self.username = settings.reddit_username
        self.password = settings.reddit_password
        self.subreddit = settings.reddit_subreddit

    async def post(self, client: httpx.AsyncClient, message: str) -> PostReceipt:
        require_configured(
            client_id=self.client_id,
            client_secret=self.client_secret,
            username=self.username,
            password=self.password,
            subreddit=self.subreddit,
        )
        token_response = await client.post(
            "https://www.reddit.com/api/v1/access_token",
            data={
                "grant_type": "password",
                "username": self.username,
                "password": self.password,
            },
            auth=httpx.BasicAuth(self.client_id or "", self.client_secret or ""),
            headers={"User-Agent": "automated-posting/1.0"},
        )
        require_success(token_response)
        access_token = response_json(token_response).get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise PostingError("Reddit did not return an access token.")

        title = message.splitlines()[0][:300]
        post_response = await client.post(
            "https://oauth.reddit.com/api/submit",
            data={
                "api_type": "json",
                "kind": "self",
                "sr": self.subreddit,
                "title": title,
                "text": message,
                "send_replies": "false",
            },
            headers={
                "Authorization": f"Bearer {access_token}",
                "User-Agent": "automated-posting/1.0",
            },
        )
        require_success(post_response)
        response_data = response_json(post_response)
        wrapper = response_data.get("json")
        if not isinstance(wrapper, dict):
            raise PostingError("Reddit returned an unexpected submission response.")
        errors = wrapper.get("errors")
        if isinstance(errors, list) and errors:
            raise PostingError("Reddit rejected the submission.")
        data = wrapper.get("data")
        if not isinstance(data, dict):
            raise PostingError("Reddit returned an unexpected submission response.")

        posted_url = data.get("url")
        if not isinstance(posted_url, str) or not posted_url:
            permalink = data.get("permalink")
            if isinstance(permalink, str) and permalink:
                posted_url = f"https://www.reddit.com{permalink}"
            else:
                raise PostingError("Reddit response was missing the post URL.")

        return PostReceipt(
            posted_url=posted_url,
            public_access=True,
            posted_at=datetime.now(timezone.utc),
        )
