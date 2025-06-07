"""Utility functions for interacting with Notion databases."""
from typing import Dict
try:
    from notion_client import Client
except ModuleNotFoundError:  # pragma: no cover - optional dependency for tests
    Client = None
from config import NOTION_TOKEN, PARENT_PAGE_ID
from logging_utils import get_logger
import notion_templates as templates

log = get_logger(__name__)

# Global notion client that other modules may reuse
if Client and NOTION_TOKEN:
    notion = Client(auth=NOTION_TOKEN)
else:  # pragma: no cover - used when notion-client not installed for tests
    notion = None


def delete_existing_databases(parent_page_id: str = PARENT_PAGE_ID) -> None:
    """Remove all child databases under the given Notion page."""
    if not notion:
        log.debug("Notion client not configured")
        return
    try:
        children = notion.blocks.children.list(parent_page_id).get("results", [])
        for block in children:
            if block["type"] == "child_database":
                notion.blocks.delete(block_id=block["id"])
                log.info("Deleted old database %s", block["id"])
    except Exception as e:
        log.error("Failed to delete databases: %s", e)


def create_database(template: Dict) -> str:
    """Create a database from a template and return its ID."""
    if not notion:
        raise RuntimeError("Notion client not configured")
    title_text = template["template_title"]
    res = notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": title_text}}],
        icon={"type": "emoji", "emoji": template.get("icon_emoji", "📄")},
        properties=template["properties"],
    )
    log.info("Created database %s", title_text)
    return res["id"]


async def create_dummy_data(db_id: str, template_title: str) -> None:
    """Insert sample rows into the given database."""
    if not notion:
        log.debug("Notion client not configured")
        return
    prop = notion.databases.retrieve(db_id)["properties"]
    if "상태" not in prop or prop["상태"]["type"] != "status":
        log.warning("Missing status column on %s", db_id)
        return

    items = templates.get_dummy_items(template_title)
    for item in items:
        props = {
            "제목": {"title": [{"text": {"content": item["제목"]}}]},
            "상태": {"status": {"name": item["상태"]}},
        }
        if "출장기간" in item:
            start, end = item["출장기간"].split("/")
            props["출장기간"] = {"date": {"start": start, "end": end}}
        notion.pages.create(parent={"database_id": db_id}, properties=props)
    log.info("Inserted %d dummy rows", len(items))

# Example usage:
# db_id = create_database(templates.DATABASE_TEMPLATES[0])
# asyncio.run(create_dummy_data(db_id, "출장 요청서"))
