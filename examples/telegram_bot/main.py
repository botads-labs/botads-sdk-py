#!/usr/bin/env python3
"""
Simple Telegram bot example built with pytelegrambotapi that forces users to
watch Botads inventory once per 5 minutes before accessing a protected feature.

The bot demonstrates two monetization flows:
- Rewarded mini app: user taps "Смотреть рекламу" and finishes the mini app campaign.
- Direct link fallback: user taps "Пропустить", receives a botads short link, and the
  webhook unlocks access after the click is confirmed.

Run:
  cd examples/telegram_bot
  pip install -r requirements.txt
  python main.py

Make sure to expose the Flask server publicly (TLS required for Telegram) and configure
webhooks to point at the endpoints defined below.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from flask import Flask, abort, request
from telebot import TeleBot, types
from telebot.apihelper import ApiException

from botads import ApiError, BotadsClient, parse_webhook_payload, verify_signature

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

if load_dotenv:
    load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Configuration via env ---------------------------------------------------
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_WEBHOOK_URL = os.getenv("TELEGRAM_WEBHOOK_URL", "")
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN", "")  # optional but recommended

WEBHOOK_LISTEN_HOST = os.getenv("WEBHOOK_LISTEN_HOST", "0.0.0.0")
WEBHOOK_LISTEN_PORT = int(os.getenv("WEBHOOK_LISTEN_PORT", "8080"))
WEBHOOK_TLS_CERT_FILE = os.getenv("WEBHOOK_TLS_CERT_FILE", "")
WEBHOOK_TLS_KEY_FILE = os.getenv("WEBHOOK_TLS_KEY_FILE", "")

BOTADS_BASE_URL = os.getenv("BOTADS_BASE_URL", "https://api.botads.app")
BOTADS_API_TOKEN = os.getenv("BOTADS_API_TOKEN", "")
if not TELEGRAM_TOKEN or ":" not in TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN is required (format: <bot_id>:<token>)")
try:
    BOTADS_TG_BOT_ID = int(TELEGRAM_TOKEN.split(":", 1)[0])
except ValueError as exc:
    raise RuntimeError("Invalid TELEGRAM_TOKEN: cannot infer bot id") from exc

MINIAPP_URL = os.getenv("MINIAPP_URL", "https://miniapp.example/launch")
DIRECT_LINK_BASE_URL = os.getenv("DIRECT_LINK_BASE_URL", "https://botads.me/")

FORCE_AD_INTERVAL_SECONDS = 5 * 60  # require ad watch once per 5 minutes

# Telegram copy
AD_PROMPT_TEXT = "Чтобы продолжить, посмотрите короткую рекламу (5 сек) 👇"
DIRECT_LINK_TEMPLATE = "Кликни на рекламу, чтобы получить доступ к боту 👇\n{url}"
UNLOCKED_TEXT = "✅ Реклама подтверждена. Можете продолжить пользоваться ботом!"


# --- State -------------------------------------------------------------------
@dataclass
class UserState:
    chat_id: int
    last_unlock_ts: float = 0.0
    direct_link_message_id: Optional[int] = None
    pending_mode: Optional[str] = None  # "rewarded" or "direct_link"
    ad_message_ids: list[int] = field(default_factory=list)


users_state: Dict[int, UserState] = {}


def get_state(user_id: int, chat_id: Optional[int] = None) -> UserState:
    state = users_state.get(user_id)
    if not state:
        if chat_id is None:
            raise KeyError(f"State for user {user_id} not found")
        state = UserState(chat_id=chat_id)
        users_state[user_id] = state
    elif chat_id and state.chat_id != chat_id:
        state.chat_id = chat_id
    return state


def requires_ad(state: UserState) -> bool:
    """Return True if the user must watch an ad before using the bot."""
    now = time.time()
    return (now - state.last_unlock_ts) >= FORCE_AD_INTERVAL_SECONDS


# --- Bot + HTTP setup --------------------------------------------------------
bot = TeleBot(TELEGRAM_TOKEN, parse_mode="HTML")
botads_client = BotadsClient(BOTADS_BASE_URL, BOTADS_API_TOKEN)
app = Flask(__name__)


def configure_telegram_webhook() -> None:
    """Set webhook so Telegram pushes updates into the Flask endpoint."""
    bot.remove_webhook()
    telegram_cert_file = os.getenv("TELEGRAM_WEBHOOK_CERT_FILE", "") or WEBHOOK_TLS_CERT_FILE
    cert = None
    if telegram_cert_file:
        cert = open(telegram_cert_file, "rb")
    try:
        bot.set_webhook(
            url=TELEGRAM_WEBHOOK_URL,
            certificate=cert,
            secret_token=TELEGRAM_SECRET_TOKEN or None,
        )
    finally:
        if cert:
            cert.close()
    log.info("Telegram webhook set to %s", TELEGRAM_WEBHOOK_URL)


# --- Business logic ----------------------------------------------------------
def handle_protected_action(message: types.Message) -> None:
    """Entry point for commands that require advertising gate."""
    user_id = message.from_user.id
    state = get_state(user_id, message.chat.id)
    if not requires_ad(state):
        bot.send_message(message.chat.id, "🎉 Секретное действие выполнено без рекламы.")
        return
    send_ad_prompt(state)


def send_ad_prompt(state: UserState) -> None:
    keyboard = types.InlineKeyboardMarkup()
    miniapp_url = f"{MINIAPP_URL}?user_tg_id={state.chat_id}"
    keyboard.add(
        types.InlineKeyboardButton(
            "Смотреть рекламу",
            web_app=types.WebAppInfo(url=miniapp_url),
        )
    )
    keyboard.add(
        types.InlineKeyboardButton("Пропустить", callback_data=f"skip:{state.chat_id}")
    )
    sent = bot.send_message(state.chat_id, AD_PROMPT_TEXT, reply_markup=keyboard)
    state.ad_message_ids.append(sent.message_id)
    state.pending_mode = "rewarded"
    log.info("Requested ad for user %s", state.chat_id)


def send_direct_link(state: UserState) -> None:
    try:
        code = botads_client.create_code(BOTADS_TG_BOT_ID, str(state.chat_id))
    except ApiError as exc:
        log.exception("Failed to fetch direct link code: %s", exc)
        bot.send_message(
            state.chat_id, "😞 Не удалось получить ссылку. Попробуйте еще раз позже."
        )
        return

    if state.direct_link_message_id:
        try:
            bot.delete_message(state.chat_id, state.direct_link_message_id)
        except ApiException:
            pass  # message might already be gone
        try:
            state.ad_message_ids.remove(state.direct_link_message_id)
        except ValueError:
            pass

    url = f"{DIRECT_LINK_BASE_URL}{code.code}"
    sent = bot.send_message(
        state.chat_id,
        DIRECT_LINK_TEMPLATE.format(url=url),
        disable_web_page_preview=True,
    )
    state.direct_link_message_id = sent.message_id
    state.ad_message_ids.append(sent.message_id)
    state.pending_mode = "direct_link"
    log.info("Sent direct link %s to user %s", url, state.chat_id)


def unlock_user(user_id: int, reason: str) -> None:
    state = users_state.get(user_id)
    if not state:
        log.warning("Webhook for unknown user %s", user_id)
        return
    state.last_unlock_ts = time.time()
    state.pending_mode = None
    for msg_id in list(state.ad_message_ids):
        try:
            bot.delete_message(state.chat_id, msg_id)
        except ApiException:
            pass
    state.ad_message_ids.clear()
    state.direct_link_message_id = None
    bot.send_message(state.chat_id, UNLOCKED_TEXT + f"\n({reason})")
    log.info("Unlocked user %s via %s", user_id, reason)


# --- Telegram handlers -------------------------------------------------------
@bot.message_handler(commands=["start"])
def handle_start(message: types.Message) -> None:
    bot.send_message(
        message.chat.id,
        "Привет! Этот бот показывает, как интегрировать Botads.\n"
        "Напишите /secret, чтобы увидеть gating в действии.",
    )
    handle_protected_action(message)


@bot.message_handler(commands=["secret"])
def handle_secret(message: types.Message) -> None:
    handle_protected_action(message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("skip:"))
def handle_skip(call: types.CallbackQuery) -> None:
    bot.answer_callback_query(call.id, "Готовим рекламную ссылку…")
    user_id = call.from_user.id
    state = get_state(user_id, call.message.chat.id)
    send_direct_link(state)


@bot.message_handler(func=lambda _: True)
def fallback(message: types.Message) -> None:
    bot.send_message(message.chat.id, "Команда не распознана. Используйте /secret.")


# --- HTTP endpoints ----------------------------------------------------------
@app.post("/telegram/webhook")
def telegram_webhook():
    if TELEGRAM_SECRET_TOKEN:
        header = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if header != TELEGRAM_SECRET_TOKEN:
            return "forbidden", 403
    update = types.Update.de_json(request.data.decode("utf-8"))
    bot.process_new_updates([update])
    return "ok"


@app.post("/botads/webhook")
def botads_webhook():
    signature = request.headers.get("X-Signature", "")
    body = request.get_data()
    if not verify_signature(body, signature, BOTADS_API_TOKEN):
        abort(401)
    payload = parse_webhook_payload(body)
    user_id = int(payload.user_tg_id)
    if payload.event == "rewarded":
        unlock_user(user_id, "миниапп просмотрена")
    elif payload.event == "direct_link":
        unlock_user(user_id, "переход по direct_link")
    else:
        log.info("Unhandled botads event %s for user %s", payload.event, user_id)
    return "ok"


def main() -> None:
    configure_telegram_webhook()
    ssl_context = None
    if WEBHOOK_TLS_CERT_FILE and WEBHOOK_TLS_KEY_FILE:
        ssl_context = (WEBHOOK_TLS_CERT_FILE, WEBHOOK_TLS_KEY_FILE)
    app.run(host=WEBHOOK_LISTEN_HOST, port=WEBHOOK_LISTEN_PORT, ssl_context=ssl_context)


if __name__ == "__main__":
    main()
