"""Entry point that orchestrates the automation flow."""
import asyncio
import traceback
from logging_utils import get_logger
from slack_utils import send_message, send_error_webhook
from notion_db_utils import (
    delete_existing_databases,
    create_database,
    create_dummy_data,
    add_relation_columns,
    notion,
)
from notion_templates import DATABASE_TEMPLATES

log = get_logger(__name__)


async def run() -> None:
    """Create Notion databases and fill them with sample data."""
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
