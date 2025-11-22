import json
import hmac
import hashlib
from dataclasses import dataclass
from typing import Any, Dict


def verify_signature(body: bytes, signature_header: str, api_token: str) -> bool:
    """
    Verify HMAC SHA-256 signature for webhook payload.

    signature_header is expected in format "sha256=<hex>".
    """
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    provided = signature_header.split("=", 1)[1]
    mac = hmac.new(api_token.encode("utf-8"), body, hashlib.sha256)
    expected = mac.hexdigest()
    return hmac.compare_digest(provided, expected)


@dataclass
class WebhookPayload:
    event: str
    user_tg_id: str
    data: Dict[str, Any]


def parse_webhook_payload(body: bytes) -> WebhookPayload:
    """Parse webhook JSON body into a typed payload."""
    payload = json.loads(body.decode("utf-8"))
    event = payload.get("event")
    user_tg_id = payload.get("user_tg_id")
    if not event or not user_tg_id:
        raise ValueError("invalid webhook payload")
    return WebhookPayload(event=event, user_tg_id=user_tg_id, data=payload)
