"""Helper functions for sending Slack notifications."""
import asyncio
import traceback
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.webhook import WebhookClient
from config import SLACK_BOT_TOKEN, SLACK_CHANNEL, SLACK_WEBHOOK_URL
from logging_utils import get_logger

log = get_logger(__name__)

slack_client = AsyncWebClient(token=SLACK_BOT_TOKEN) if SLACK_BOT_TOKEN else None
webhook_client = WebhookClient(SLACK_WEBHOOK_URL) if SLACK_WEBHOOK_URL else None


async def send_message(text: str, channel: str = SLACK_CHANNEL) -> None:
    """Post a simple message to Slack."""
    if not slack_client:
        log.debug("Slack client not configured")
        return
    try:
        await slack_client.chat_postMessage(channel=channel, text=text)
        log.info("Sent Slack message to %s", channel)
    except Exception as e:
        log.error("Slack API error: %s", e)


def send_error_webhook(exc: BaseException) -> None:
    """Send an exception traceback via incoming webhook."""
    if not webhook_client:
        return
    trace_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        webhook_client.send(text=f"❗️ Error occurred\n```{trace_text}```")
    except Exception as err:
        log.error("Webhook send failed: %s", err)

# Example usage:
# await send_message("hello")
