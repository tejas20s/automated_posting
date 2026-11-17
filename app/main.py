from fastapi import FastAPI

from app.schemas import PostingRequest, PostingResponse
from app.services.posting_service import post_message

app = FastAPI(
    title="Automated Posting API",
    description="Publish a validated message to configured social platforms.",
    version="1.0.0",
)


@app.post("/posting", response_model=PostingResponse)
async def posting(request: PostingRequest) -> PostingResponse:
    return await post_message(request.message)
