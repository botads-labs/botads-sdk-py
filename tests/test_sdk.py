import asyncio
import hashlib
import hmac
import json
import unittest

from botads import (
    AsyncBotadsClient,
    BotadsClient,
    CodeResponse,
    DEFAULT_API_BASE_URL,
    DEFAULT_DIRECT_LINK_BASE_URL,
    EVENT_DIRECT_LINK,
    EVENT_REWARDED,
    parse_webhook_payload,
    verify_signature,
)


class TestSDK(unittest.TestCase):
    def test_event_constants(self) -> None:
        self.assertEqual(EVENT_DIRECT_LINK, "direct_link")
        self.assertEqual(EVENT_REWARDED, "rewarded")

    def test_verify_signature_ok(self) -> None:
        token = "test-token"
        body = b'{"event":"rewarded","user_tg_id":"123","data":{"x":1}}'
        digest = hmac.new(token.encode("utf-8"), body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_signature(body, f"sha256={digest}", token))

    def test_verify_signature_invalid_header(self) -> None:
        headers = ["", "sha1=deadbeef", "sha256=", "sha256=deadbeef"]
        for header in headers:
            with self.subTest(header=header):
                self.assertFalse(verify_signature(b"{}", header, "token"))

    def test_parse_webhook_payload(self) -> None:
        body = json.dumps({"event": EVENT_DIRECT_LINK, "user_tg_id": "42", "foo": "bar"}).encode(
            "utf-8"
        )
        payload = parse_webhook_payload(body)
        self.assertEqual(payload.event, EVENT_DIRECT_LINK)
        self.assertEqual(payload.user_tg_id, "42")
        self.assertEqual(payload.data["foo"], "bar")

    def test_parse_webhook_payload_invalid(self) -> None:
        payloads = [{}, {"event": EVENT_DIRECT_LINK}, {"user_tg_id": "1"}]
        for payload in payloads:
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    parse_webhook_payload(json.dumps(payload).encode("utf-8"))

    def test_code_response_direct_link_default(self) -> None:
        code = CodeResponse(code="AAATEST", expires_in=3600, expires_at="2025-01-01T00:00:00Z")
        self.assertEqual(code.direct_link, f"{DEFAULT_DIRECT_LINK_BASE_URL}/AAATEST")
        self.assertEqual(code.direct_link_url("https://example.com/"), "https://example.com/AAATEST")

    def test_sync_client_default_base_url(self) -> None:
        client = BotadsClient(api_token="token")
        try:
            self.assertEqual(client.base_url, DEFAULT_API_BASE_URL)
        finally:
            client.close()

    def test_sync_client_requires_token(self) -> None:
        with self.assertRaises(ValueError):
            BotadsClient()

    def test_async_client_default_base_url(self) -> None:
        client = AsyncBotadsClient(api_token="token")
        try:
            self.assertEqual(client.base_url, DEFAULT_API_BASE_URL)
        finally:
            asyncio.run(client.aclose())

    def test_async_client_requires_token(self) -> None:
        with self.assertRaises(ValueError):
            AsyncBotadsClient()
