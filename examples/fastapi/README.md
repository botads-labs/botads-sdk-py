# FastAPI Webhook Demo (Botads)

Minimal FastAPI webhook handler example:

- Verifies `X-Signature` (HMAC SHA-256)
- Parses the webhook payload
- Shows how to issue short codes via the Client API

## Quick Start

1. Install deps:

```bash
cd sdks/python
pip install -r requirements.txt
pip install fastapi uvicorn
```

2. Create `.env` from the template:

```bash
cd examples/fastapi
cp .env.example .env
```

Fill **all** fields in `.env.example` (copy it to `.env` and replace the values with your own).

3. Run:

```bash
uvicorn main:app --host 0.0.0.0 --port 8082
```

4. Health endpoint:

```bash
curl http://localhost:8082/health
```
