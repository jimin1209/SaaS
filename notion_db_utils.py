"""Utility functions for interacting with Notion databases."""
from typing import Dict, List, Optional
try:
    from notion_client import Client
except ModuleNotFoundError:  # pragma: no cover - optional dependency for tests
    Client = None
from config import NOTION_TOKEN, PARENT_PAGE_ID
from logging_utils import get_logger
import notion_templates as templates

log = get_logger(__name__)

# 기본 상태 옵션과 색상을 정의
# Notion API에서 지원하는 색상값이 바뀌면 아래 리스트만 수정하면 됩니다.
DEFAULT_STATUS_OPTIONS = [
    {"name": "미처리", "color": "default"},
    {"name": "진행중", "color": "orange"},
    {"name": "완료", "color": "green"},
    {"name": "반려", "color": "red"},
]
DEFAULT_STATUS_NAME = "미처리"

# Global notion client that other modules may reuse
if Client and NOTION_TOKEN:
    notion = Client(auth=NOTION_TOKEN)
else:  # pragma: no cover - used when notion-client not installed for tests
    notion = None


def ensure_status_column(
    db_id: str,
    *,
    options: Optional[List[Dict[str, str]]] = None,
    default_name: Optional[str] = None,
) -> None:
    """Ensure the given database has a styled ``상태`` status property.

    # 변경 포인트: Notion API에서 status 속성 구조가 바뀌면 아래 옵션 구성
    # ``status_cfg`` 부분만 수정하면 된다.

    Parameters
    ----------
    db_id:
        ID of the database to update.
    options:
        List of status option dictionaries with ``name`` and ``color`` keys.
        ``DEFAULT_STATUS_OPTIONS`` is used when omitted.
    default_name:
        Default status name to apply. ``DEFAULT_STATUS_NAME`` when omitted.

    This helper is used right after creating a database as some templates may
    miss the column or have it defined with a wrong type. If the column is
    missing or not a ``status`` property it will be recreated using
    ``databases.update`` with the given options.
    """
    if not notion:
        log.debug("Notion client not configured")
        return
    try:
        info = notion.databases.retrieve(db_id)
        prop = info.get("properties", {}).get("상태")
        need_update = not prop or prop.get("type") != "status"
        if need_update:
            status_cfg = {"options": options or DEFAULT_STATUS_OPTIONS}
            name = default_name or DEFAULT_STATUS_NAME
            if name:
                status_cfg["default"] = {"name": name}
            notion.databases.update(db_id, properties={"상태": {"status": status_cfg}})
            log.info("Ensured status column on %s", db_id)
    except Exception as exc:  # pragma: no cover - network failures
        log.error("Failed to ensure status column on %s: %s", db_id, exc)


def delete_existing_databases(parent_page_id: str = PARENT_PAGE_ID) -> None:
    """Remove all child databases under the given Notion page."""
    if not notion:
        log.debug("Notion client not configured")
        return
    try:
        cursor = None
        while True:
            if cursor:
                page = notion.blocks.children.list(parent_page_id, start_cursor=cursor)
            else:
                page = notion.blocks.children.list(parent_page_id)
            children = page.get("results", [])
            for block in children:
                if block.get("type") == "child_database":
                    notion.blocks.delete(block_id=block["id"])
                    log.info("Deleted old database %s", block["id"])
            cursor = page.get("next_cursor")
            if not cursor:
                break
    except Exception as e:
        log.error("Failed to delete databases: %s", e)


def create_database(template: Dict) -> str:
    """Create a database from a template and return its ID."""
    if not notion:
        raise RuntimeError("Notion client not configured")
    title_text = template["template_title"]
    properties = {}
    for name, prop in template["properties"].items():
        # Remove helper keys not supported by Notion
        prop = {k: v for k, v in prop.items() if k != "target_template"}
        # Notion requires relation properties to specify the target database.
        # Templates may leave the relation config empty so skip it for now and
        # create it in a second step once all databases exist.
        if prop.get("relation") == {}:
            log.debug("Skipping relation property %s for %s", name, title_text)
            continue
        properties[name] = prop

    res = notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": title_text}}],
        icon={"type": "emoji", "emoji": template.get("icon_emoji", "📄")},
        properties=properties,
    )
    log.info("Created database %s", title_text)
    db_id = res["id"]
    # Ensure the status column exists right after creation
    ensure_status_column(db_id)
    return db_id


async def create_dummy_data(db_id: str, template_title: str) -> None:
    """Insert sample rows into the given database."""
    if not notion:
        log.debug("Notion client not configured")
        return
    # Verify the status column exists before inserting sample rows
    ensure_status_column(db_id)
    prop = notion.databases.retrieve(db_id)["properties"]
    if "상태" not in prop or prop["상태"].get("type") != "status":
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

def add_relation_columns(db_id_map: Dict[str, str]) -> None:
    """Update databases with relation properties once all IDs are known."""
    if not notion:
        log.debug("Notion client not configured")
        return

    for tmpl in templates.DATABASE_TEMPLATES:
        db_id = db_id_map.get(tmpl["template_title"])
        if not db_id:
            continue

        updates = {}
        for name, prop in tmpl["properties"].items():
            if prop.get("relation") == {}:
                target_title = prop.get("target_template")
                target_id = db_id_map.get(target_title)
                if target_id:
                    updates[name] = {
                        "relation": {
                            "database_id": target_id,
                            "type": "single_property",
                            "single_property": {},
                        }
                    }
                else:
                    log.warning(
                        "Relation target %s for %s missing", target_title, name
                    )

        if updates:
            try:
                notion.databases.update(db_id, properties=updates)
                log.info("Updated relations for %s", tmpl["template_title"])
            except Exception as exc:
                log.error("Failed to update relations on %s: %s", db_id, exc)

# Example usage:
# db_id = create_database(templates.DATABASE_TEMPLATES[0])
# asyncio.run(create_dummy_data(db_id, "출장 요청서"))
