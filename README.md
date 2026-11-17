
# Automated Posting API

A small FastAPI service. You send it one short message with a link, and it posts that message to Mastodon, Bluesky, Reddit, Telegram and Discord.

Each platform is tried on its own, so if one is down or you haven't set it up, the rest still go out.

## What you need

- Python 3.10 or newer
- Credentials for whichever platforms you want to use (you don't need all five)

## Running it locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill in the platform values in `.env`, then start the server:

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 4000 --env-file .env
```

Swagger docs are at [http://localhost:4000/docs](http://localhost:4000/docs) if you want to poke around.

When you deploy, pass secrets in through the environment rather than shipping a `.env` file.

## Making a request

```http
POST /posting
Content-Type: application/json
```

```json
{
  "message": "Check out our latest business platform and grow your online visibility. https://example.com"
}
```

Rules for `message`: 1 to 200 characters, and it must contain exactly one valid HTTP(S) link. You can't choose platforms in the request. Every valid request goes to all five.

## What you get back

```json
{
  "success": true,
  "results": [
    {
      "platform": "Mastodon",
      "status": "success",
      "posted_url": "https://mastodon.social/@account/123",
      "published_content": "Check out our latest business platform and grow your online visibility. https://example.com",
      "public_access": true,
      "date": "2026-11-17",
      "time": "05:59:00",
      "error": null
    },
    {
      "platform": "Bluesky",
      "status": "failed",
      "posted_url": null,
      "published_content": null,
      "public_access": false,
      "date": null,
      "time": null,
      "error": "Platform credentials or target are not configured."
    }
  ]
}
```

That's just a sample to show the shape, not real output.

A few things worth knowing:

- `success` is `true` if at least one platform worked.
- Dates and times are UTC.
- Discord always shows `public_access: false`, since whether someone can see the message depends on their server membership and channel permissions. You still get a permalink back when Discord gives us the IDs to build one.

## Setting up each platform

- **Mastodon:** you need your instance's API base URL and an access token with the `write:statuses` scope. Posts are explicitly sent as `public`. ([docs](https://docs.joinmastodon.org/methods/statuses/#create))
- **Bluesky:** use your handle (or DID) and an app password. The service opens a session and writes an `app.bsky.feed.post` record. ([docs](https://docs.bsky.app/docs/api/com-atproto-repo-create-record))
- **Reddit:** create a script-type OAuth app, then provide the app credentials, your account login and the subreddit to post in. Reddit can still turn a post down because of subreddit rules, permissions or account restrictions. ([docs](https://www.reddit.com/dev/api/))
- **Telegram:** provide a bot token and the public username of your channel. The bot has to be allowed to post there. ([docs](https://core.telegram.org/bots/api#sendmessage))
- **Discord:** just an incoming webhook URL. If the webhook response doesn't include guild and channel IDs, you can set them yourself. ([docs](https://docs.discord.com/developers/resources/webhook#execute-webhook))

Missing credentials won't stop the server from starting. That platform just comes back as failed with a config error in its result.

And please don't commit `.env` or any real credentials.

## Tests

```powershell
pip install -r requirements-dev.txt
pytest
```
=======
# automated_posting

