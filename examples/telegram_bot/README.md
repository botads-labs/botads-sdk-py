# Telegram Bot Demo (BotAds)

This example shows how to:

- Gate a bot action behind an ad view (rewarded miniapp) or a direct link fallback.
- Receive Botads webhooks and verify the signature.
- Run a Telegram webhook server with TLS (Telegram requires HTTPS).

## Quick Start

1. Install dependencies:

```bash
cd sdks/python/examples/telegram_bot
pip install -r requirements.txt
```

2. Create `.env` from the template:

```bash
cp .env.example .env
```

Fill **all** fields in `.env.example` (copy it to `.env` and replace the values with your own).

3. Generate a self-signed TLS cert for your public domain (or use a real cert):

```bash
./generate_selfsigned.sh your-domain.example
```

This writes:

- `certs/webhook.crt`
- `certs/webhook.key`

and the app will:

- Serve HTTPS using `WEBHOOK_TLS_CERT_FILE`/`WEBHOOK_TLS_KEY_FILE`
- Upload the cert to Telegram when calling `setWebhook` (needed for self-signed)

4. Run:

```bash
python main.py
```

## Webhook Endpoints

- Telegram webhook: `POST /telegram/webhook`
- Botads webhook: `POST /botads/webhook`

## Notes

- For `direct_link` messages, link previews must be disabled. Telegram can fetch the URL
  to build a preview which may accidentally trigger tracking/redirect logic as if the
  user clicked the link.
- Useful commands in the bot:
  - `/bonus` — run the gated action
  - `/reset_ad` — reset the ad timer (forces gating on next `/bonus`)
