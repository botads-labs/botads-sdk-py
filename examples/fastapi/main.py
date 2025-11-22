from fastapi import FastAPI, Header, HTTPException, Request
from botads import AsyncBotadsClient, verify_signature, parse_webhook_payload

app = FastAPI()

# Replace with real values or use env vars
BOT_API_TOKEN = "BOT_API_TOKEN"
BOT_ID = 123456789
CLIENT_BASE_URL = "http://localhost:8080"

client = AsyncBotadsClient(base_url=CLIENT_BASE_URL, api_token=BOT_API_TOKEN)


async def issue_short_code(user_tg_id: str):
    """Example helper to request a short code."""
    return await client.create_code(bot_id=BOT_ID, user_tg_id=user_tg_id)


@app.post("/webhook")
async def webhook(request: Request, x_signature: str = Header(None), x_bot_id: str = Header(None)):
    body = await request.body()
    if not verify_signature(body, x_signature or "", BOT_API_TOKEN):
        raise HTTPException(status_code=401, detail="invalid signature")
    payload = parse_webhook_payload(body)
    # process payload.event / payload.user_tg_id / payload.data
    return {"status": "ok"}


@app.on_event("shutdown")
async def shutdown():
    await client.aclose()
