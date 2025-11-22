# botads SDK Python

Пакет `botads-sdk` предоставляет обёртки для Client API Botads и утилиты для обработки вебхуков.

## Возможности

| Компонент                       | Методы / структуры                                   | Назначение                                |
|---------------------------------|------------------------------------------------------|-------------------------------------------|
| `BotadsClient`                  | `create_code(bot_id, user_tg_id) -> CodeResponse`    | Синхронный вызов Client API               |
| `AsyncBotadsClient`             | `create_code(...)`                                   | Асинхронный вариант (aio/httpx)           |
| Модели                          | `CodeResponse`, `ApiError`, `WebhookPayload`         | Типизированные ответы и ошибки            |
| Вебхук утилиты                  | `verify_signature(body, signature, token)`<br>`parse_webhook_payload(body)` | HMAC SHA-256 проверка и парсинг события |
| Примеры                         | `sdks/python/examples/fastapi/main.py`               | Демонстрация async webhook handler + выдача short code |

Все ошибки, которые возвращает Client API, описаны в публичной документации (`docs/public/content/api/central.mdx`). SDK мапит их в `ApiError`.

## Структура проекта

- `botads/client.py` — синхронный клиент (requests).
- `botads/async_client.py` — асинхронный клиент (httpx).
- `botads/webhook.py` — HMAC-подпись, `WebhookPayload`.
- `examples/fastapi/main.py` — пример использования.

## Установка

Стабильную версию можно поставить напрямую из PyPI:

```bash
pip install botads-sdk
```

Локально можно установить из исходников для разработки/отладки:

```bash
cd sdks/python
pip install -r requirements.txt
```

## TODO

- Настроить CI (lint/tests) и автоматическую публикацию `botads-sdk` в PyPI.
- Расширять список методов по мере появления новых возможностей Client API.

## Релиз / разработка

- Перед релизом убедитесь, что версия в `botads/__init__.py` и `pyproject.toml` обновлена.
- Локальная сборка: `pip install build && python3 -m build` (создаёт `dist/`).
- Публикация: `python3 -m twine upload dist/*` (потребует `TWINE_USERNAME/ PASSWORD`).

Детальное руководство по использованию появится в GitBook (раздел SDK) после первого публичного релиза. Пока ориентируйтесь на этот README и код примеров.
