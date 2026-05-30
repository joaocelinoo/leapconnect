"""Telegram notifier implementation using the Bot API via httpx."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from io import BytesIO

import httpx

from . import BaseNotifier, Notification

_LOGGER = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org/bot{token}"


class TelegramNotifier(BaseNotifier):
    """Sends notifications via Telegram Bot API."""

    def __init__(self, bot_token: str, chat_id: str) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._base_url = TELEGRAM_API_BASE.format(token=bot_token)
        self._callback_handler: asyncio.Task | None = None
        self._callback_listeners: dict[
            str, object
        ] = {}  # callback_data_prefix -> dispatcher ref
        self._last_update_id: int = 0

    async def send(self, notification: Notification) -> bool:
        """Send a text message with HTML formatting."""
        text = self._format_message(notification)
        payload = {
            "chat_id": self._chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        # Add inline keyboard if provided
        if notification.extra.get("reply_markup"):
            payload["reply_markup"] = notification.extra["reply_markup"]
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{self._base_url}/sendMessage", json=payload)
                if resp.status_code == 200:
                    return True
                _LOGGER.warning(
                    "Telegram sendMessage failed: %d %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return False
        except Exception as exc:
            _LOGGER.error("Telegram send error: %s", exc)
            return False

    async def send_photo(self, notification: Notification) -> bool:
        """Send a photo with caption."""
        if not notification.image:
            return await self.send(notification)

        caption = self._format_message(notification)
        # Telegram caption limit is 1024 chars
        if len(caption) > 1024:
            caption = caption[:1020] + "..."

        files = {
            "photo": ("vehicle.png", BytesIO(notification.image), "image/png"),
        }
        data = {
            "chat_id": self._chat_id,
            "caption": caption,
            "parse_mode": "HTML",
        }
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self._base_url}/sendPhoto", data=data, files=files
                )
                if resp.status_code == 200:
                    return True
                _LOGGER.warning(
                    "Telegram sendPhoto failed: %d %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return False
        except Exception as exc:
            _LOGGER.error("Telegram send_photo error: %s", exc)
            return False

    async def test_connection(self) -> tuple[bool, str]:
        """Send a test message to verify bot configuration."""
        payload = {
            "chat_id": self._chat_id,
            "text": (
                "✅ <b>LeapConnect</b> — Notifications active!\n\n"
                "Connection configured successfully."
            ),
            "parse_mode": "HTML",
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{self._base_url}/sendMessage", json=payload)
                if resp.status_code == 200:
                    return True, "Test message sent successfully"
                data = (
                    resp.json()
                    if resp.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                )
                description = data.get("description", resp.text[:100])
                return False, f"Telegram error: {description}"
        except httpx.TimeoutException:
            return False, "Connection timeout to Telegram"
        except Exception as exc:
            return False, f"Error: {exc}"

    @staticmethod
    def _format_message(notification: Notification) -> str:
        """Build an HTML-formatted Telegram message."""
        parts = []
        parts.append(f"<b>{notification.title}</b>")
        if notification.body:
            parts.append(notification.body)
        return "\n".join(parts)

    async def send_location(
        self,
        lat: float,
        lon: float,
        caption: str = "",
        reply_markup: dict | None = None,
    ) -> bool:
        """Send a native Telegram location message with optional inline keyboard."""
        payload: dict = {
            "chat_id": self._chat_id,
            "latitude": lat,
            "longitude": lon,
        }
        if reply_markup:
            payload["reply_markup"] = json.dumps(reply_markup)
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(f"{self._base_url}/sendLocation", json=payload)
                if resp.status_code == 200:
                    return True
                _LOGGER.warning(
                    "Telegram sendLocation failed: %d %s",
                    resp.status_code,
                    resp.text[:200],
                )
                return False
        except Exception as exc:
            _LOGGER.error("Telegram send_location error: %s", exc)
            return False

    async def answer_callback_query(
        self, callback_query_id: str, text: str = ""
    ) -> None:
        """Acknowledge a callback query."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(
                    f"{self._base_url}/answerCallbackQuery",
                    json={
                        "callback_query_id": callback_query_id,
                        "text": text,
                    },
                )
        except Exception as exc:
            _LOGGER.debug("answer_callback_query error: %s", exc)

    def start_callback_polling(self, dispatcher) -> None:
        """Start a background task that polls for Telegram callback_query updates."""
        if self._callback_handler and not self._callback_handler.done():
            return
        self._callback_listeners["stop_tracking:"] = dispatcher
        self._callback_handler = asyncio.create_task(self._poll_callbacks())

    def stop_callback_polling(self) -> None:
        """Stop the callback polling task."""
        if self._callback_handler and not self._callback_handler.done():
            self._callback_handler.cancel()
            self._callback_handler = None

    async def _poll_callbacks(self) -> None:
        """Long-poll Telegram for callback_query updates."""
        _LOGGER.info("Telegram callback polling started")
        try:
            while True:
                try:
                    async with httpx.AsyncClient(timeout=35) as client:
                        params = {
                            "timeout": 30,
                            "allowed_updates": '["callback_query"]',
                        }
                        if self._last_update_id:
                            params["offset"] = self._last_update_id + 1
                        resp = await client.get(
                            f"{self._base_url}/getUpdates", params=params
                        )
                        if resp.status_code != 200:
                            await asyncio.sleep(5)
                            continue
                        data = resp.json()
                        for update in data.get("result", []):
                            self._last_update_id = update["update_id"]
                            cq = update.get("callback_query")
                            if not cq:
                                continue
                            cb_data = cq.get("data", "")
                            # Handle stop_tracking callbacks
                            if cb_data.startswith("stop_tracking:"):
                                vin = cb_data.split(":", 1)[1]
                                dispatcher = self._callback_listeners.get(
                                    "stop_tracking:"
                                )
                                if dispatcher:
                                    stopped = await dispatcher.stop_tracking(vin)
                                    ack_text = (
                                        "✅ Tracking stopped"
                                        if stopped
                                        else "⚠️ Tracking was not active"
                                    )
                                    await self.answer_callback_query(cq["id"], ack_text)
                                    # Edit original message to reflect stopped state
                                    if cq.get("message"):
                                        with contextlib.suppress(Exception):
                                            await client.post(
                                                f"{self._base_url}/editMessageReplyMarkup",
                                                json={
                                                    "chat_id": cq["message"]["chat"][
                                                        "id"
                                                    ],
                                                    "message_id": cq["message"][
                                                        "message_id"
                                                    ],
                                                    "reply_markup": {
                                                        "inline_keyboard": []
                                                    },
                                                },
                                            )
                                else:
                                    await self.answer_callback_query(
                                        cq["id"], "⚠️ Not available"
                                    )
                except httpx.TimeoutException:
                    continue
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    _LOGGER.warning("Callback poll error: %s", exc)
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            _LOGGER.info("Telegram callback polling stopped")
        except Exception as exc:
            _LOGGER.error("Callback polling fatal: %s", exc)
