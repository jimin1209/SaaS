"""Helper functions for sending Slack notifications."""
import asyncio
import traceback
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.webhook import WebhookClient
from config import (
    SLACK_BOT_TOKEN,
    SLACK_CHANNEL,
    SLACK_WEBHOOK_URL,
    SLACK_ERROR_WEBHOOK_URL,
)
import logging
from logging_utils import get_logger

log = get_logger(__name__)

slack_client = AsyncWebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None
webhook_client = WebhookClient(SLACK_WEBHOOK_URL) if SLACK_WEBHOOK_URL else None


async def send_message(text: str, channel: str = SLACK_CHANNEL) -> None:
    """Post a simple message to Slack."""
    if not slack_client:
        log.debug("슬랙 클라이언트 미설정")
        return
    try:
        await slack_client.chat_postMessage(channel=channel, text=text)
        log.info("%s 채널로 슬랙 메시지 전송", channel)
    except Exception as e:
        log.error("슬랙 API 오류: %s", e)


def send_error_webhook(exc: BaseException) -> None:
    """Send an exception traceback via incoming webhook."""
    if not webhook_client:
        return
    trace_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        webhook_client.send(text=f"❗️ 오류 발생\n```{trace_text}```")
    except Exception as err:
        log.error("웹훅 전송 실패: %s", err)


class SlackLogHandler(logging.Handler):
    """Logging handler that posts records to Slack via webhook."""

    EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "✅",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "💥",
    }

    def __init__(self) -> None:
        super().__init__()
        self.webhook = WebhookClient(SLACK_WEBHOOK_URL) if SLACK_WEBHOOK_URL else None
        self.error_webhook = (
            WebhookClient(SLACK_ERROR_WEBHOOK_URL)
            if SLACK_ERROR_WEBHOOK_URL
            else None
        )

    def emit(self, record: logging.LogRecord) -> None:
        if not self.webhook:
            return
        prefix = self.EMOJIS.get(record.levelno, "")
        text = f"{prefix} {self.format(record)}"
        try:
            self.webhook.send(text=text)
            if record.levelno >= logging.ERROR and self.error_webhook:
                self.error_webhook.send(text=text)
        except Exception as exc:  # pragma: no cover - network errors
            log.error("SlackLogHandler 오류: %s", exc)


class SlackLogHandler(logging.Handler):
    """Logging handler that posts records to Slack via webhook."""

    EMOJIS = {
        logging.DEBUG: "🔍",
        logging.INFO: "✅",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "💥",
    }

    def __init__(self) -> None:
        super().__init__()
        self.webhook = WebhookClient(SLACK_WEBHOOK_URL) if SLACK_WEBHOOK_URL else None
        self.error_webhook = (
            WebhookClient(SLACK_ERROR_WEBHOOK_URL)
            if SLACK_ERROR_WEBHOOK_URL
            else None
        )

    def emit(self, record: logging.LogRecord) -> None:
        if not self.webhook:
            return
        prefix = self.EMOJIS.get(record.levelno, "")
        text = f"{prefix} {self.format(record)}"
        try:
            self.webhook.send(text=text)
            if record.levelno >= logging.ERROR and self.error_webhook:
                self.error_webhook.send(text=text)
        except Exception as exc:  # pragma: no cover - network errors
            log.error("SlackLogHandler failed: %s", exc)

# Example usage:
# await send_message("hello")
