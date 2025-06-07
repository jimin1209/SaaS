"""Entry point that orchestrates the automation flow."""
import asyncio
import traceback
from logging_utils import get_logger
from slack_utils import send_message, send_error_webhook, SlackLogHandler
import logging
from config import LOG_LEVEL
from notion_db_utils import (
    delete_existing_databases,
    create_database,
    create_dummy_data,
    add_relation_columns,
    notion,
)
from notion_templates import DATABASE_TEMPLATES

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
slack_handler = SlackLogHandler()
slack_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
root_logger.addHandler(slack_handler)
log = get_logger(__name__)


async def run() -> None:
    """Create Notion databases and fill them with sample data.

    ``create_database`` automatically verifies that a ``상태`` status column
    exists on each newly created database so that subsequent calls that rely on
    this field do not fail. 기본 옵션은 ``미처리/진행중/완료/반려``이며 필요한 경우
    ``ensure_status_column`` 호출 시 다른 기본값을 지정할 수 있습니다.
    """
    if not notion:
        log.warning("Notion client not configured; skipping database creation")
        await send_message("⚠️ Notion credentials missing")
        return
    delete_existing_databases()
    db_ids = {}
    for tmpl in DATABASE_TEMPLATES:
        db_id = create_database(tmpl)
        db_ids[tmpl["template_title"]] = db_id

    add_relation_columns(db_ids)

    for tmpl in DATABASE_TEMPLATES:
        await create_dummy_data(db_ids[tmpl["template_title"]], tmpl["template_title"])
        
    await send_message("✅ Notion automation complete")


def main() -> None:
    try:
        asyncio.run(run())
    except Exception as exc:
        log.error("Unhandled error: %s", exc)
        send_error_webhook(exc)
        raise


if __name__ == "__main__":
    main()
