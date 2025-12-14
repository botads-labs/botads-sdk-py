import os

from fastapi import FastAPI, Header, HTTPException, Request

from botads import (
    AsyncBotadsClient,
    parse_webhook_payload,
    verify_signature,
)

BOT_API_TOKEN = os.getenv("BOT_API_TOKEN", "BOT_API_TOKEN")
BOT_ID = os.getenv("BOT_ID", "123456789")

app = FastAPI()
client = AsyncBotadsClient(api_token=BOT_API_TOKEN)


@app.get("/health")
async def health():
    return {"status": "ok"}


async def issue_short_code(user_tg_id: str):
    """Example helper to request a short code."""
    return await client.create_code(bot_id=BOT_ID, user_tg_id=user_tg_id)


@app.post("/webhook")
async def webhook(
    request: Request,
    x_signature: str = Header(default=""),
    x_bot_id: str = Header(default=""),
):
    body = await request.body()
    if BOT_ID and x_bot_id and BOT_ID != x_bot_id:
        raise HTTPException(status_code=401, detail="bot_id mismatch")
    if not verify_signature(body, x_signature or "", BOT_API_TOKEN):
        raise HTTPException(status_code=401, detail="invalid signature")
    payload = parse_webhook_payload(body)
    # process payload.event / payload.user_tg_id / payload.data
    print(
        {"event": payload.event, "user_tg_id": payload.user_tg_id, "data": payload.data},
        flush=True,
    )
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await client.aclose()
