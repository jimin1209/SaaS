"""Utility functions for interacting with Notion databases."""
from typing import Dict, List, Optional
try:
    from notion_client import Client
except ModuleNotFoundError:  # pragma: no cover - optional dependency for tests
    Client = None
from config import NOTION_TOKEN, PARENT_PAGE_ID, DEFAULT_USER_ID
from logging_utils import get_logger
import notion_templates as templates
from google_calendar_utils import create_event

log = get_logger(__name__)

# 기본 상태 옵션과 색상을 정의
# ``status`` 속성 대신 ``select`` 타입을 사용하여 상태값을 관리한다.
# Notion API에서 지원하는 색상값이 바뀌면 아래 리스트만 수정하면 됩니다.
DEFAULT_SELECT_OPTIONS = [
    {"name": "미처리", "color": "default"},
    {"name": "진행중", "color": "yellow"},
    {"name": "완료", "color": "green"},
    {"name": "반려", "color": "red"},
]
DEFAULT_SELECT_NAME = "미처리"

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
    """Ensure the given database has a styled ``상태`` select property.

    # 변경 포인트: Notion API에서 status 속성 구조가 바뀌면 아래 옵션 구성
    # ``status_cfg`` 부분만 수정하면 된다.

    Parameters
    ----------
    db_id:
        ID of the database to update.
    options:
        List of select option dictionaries with ``name`` and ``color`` keys.
        ``DEFAULT_SELECT_OPTIONS`` is used when omitted.
    default_name:
        Default select name to apply when creating new property.
        ``DEFAULT_SELECT_NAME`` when omitted.

    This helper is used right after creating a database as some templates may
    miss the column or have it defined with a wrong type. If the column is
    missing or not a ``select`` property it will be recreated using
    ``databases.update`` with the given options.
    """
    if not notion:
        log.debug("노션 클라이언트 미설정")
        return
    try:
        info = notion.databases.retrieve(db_id)
        prop = info.get("properties", {}).get("상태")
        need_update = not prop or prop.get("type") != "select"
        if need_update:
            select_cfg = {"options": options or DEFAULT_SELECT_OPTIONS}
            name = default_name or DEFAULT_SELECT_NAME
            if name:
                select_cfg["default"] = {"name": name}
            notion.databases.update(db_id, properties={"상태": {"select": select_cfg}})
            log.info("상태(select) 컬럼을 보정했습니다: %s", db_id)
    except Exception as exc:  # pragma: no cover - network failures
        log.error("상태 컬럼 보정 실패: %s - %s", db_id, exc)


def delete_existing_databases(parent_page_id: str = PARENT_PAGE_ID) -> None:
    """Remove all child databases under the given Notion page."""
    if not notion:
        log.debug("노션 클라이언트 미설정")
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
                    log.info("기존 데이터베이스 %s 삭제", block["id"])
            cursor = page.get("next_cursor")
            if not cursor:
                break
    except Exception as e:
        log.error("데이터베이스 삭제 실패: %s", e)


def create_database(template: Dict) -> str:
    """Create a database from a template and return its ID."""
    if not notion:
        raise RuntimeError("노션 클라이언트가 설정되지 않았습니다")
    title_text = template["template_title"]
    properties = {}
    for name, prop in template["properties"].items():
        # Remove helper keys not supported by Notion
        prop = {k: v for k, v in prop.items() if k != "target_template"}
        # Notion requires relation properties to specify the target database.
        # Templates may leave the relation config empty so skip it for now and
        # create it in a second step once all databases exist.
        if prop.get("relation") == {}:
            log.debug("relation 속성 %s(%s) 은 후처리 단계에서 생성", name, title_text)
            continue
        properties[name] = prop

    res = notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": title_text}}],
        icon={"type": "emoji", "emoji": template.get("icon_emoji", "📄")},
        properties=properties,
    )
    log.info("데이터베이스 %s 생성 완료", title_text)
    db_id = res["id"]
    # Ensure the status column exists right after creation
    ensure_status_column(db_id)
    return db_id


async def create_dummy_data(
    db_id: str,
    template_title: str,
    related_page_ids: Optional[List[str]] = None,
) -> List[str]:
    """Insert sample rows and return created page IDs."""
    if not notion:
        log.debug("노션 클라이언트 미설정")
        return
    # Verify the status column exists before inserting sample rows
    ensure_status_column(db_id)
    prop = notion.databases.retrieve(db_id)["properties"]
    if "상태" not in prop or prop["상태"].get("type") != "select":
        log.warning("상태(select) 컬럼이 없어 생성을 건너뜁니다: %s", db_id)
        return

    tmpl = templates.get_template(template_title) or {}
    items = templates.get_dummy_items(template_title)
    page_ids: List[str] = []
    for item in items:
        props: Dict[str, Dict] = {}
        for key, value in item.items():
            pdef = tmpl.get("properties", {}).get(key, {})
            ptype = next(iter(pdef.keys()), None)
            if ptype == "title":
                props[key] = {"title": [{"text": {"content": value}}]}
            elif ptype == "select":
                props[key] = {"select": {"name": value}}
            elif ptype == "date" and isinstance(value, str):
                if key == "출장기간" and "/" in value:
                    start, end = value.split("/")
                    props[key] = {"date": {"start": start, "end": end}}
                else:
                    props[key] = {"date": {"start": value}}
            elif ptype == "number":
                props[key] = {"number": value}
            elif ptype == "files":
                props[key] = {"files": value}
            elif ptype == "people":
                people_ids = []
                for person in value:
                    pid = person.get("id")
                    if pid == "dummy-user" and DEFAULT_USER_ID:
                        people_ids.append({"id": DEFAULT_USER_ID})
                    elif pid and pid != "dummy-user":
                        people_ids.append({"id": pid})
                if people_ids:
                    props[key] = {"people": people_ids}
            elif ptype == "relation":
                ids = value if isinstance(value, list) else [value]
                real_ids = []
                for rid in ids:
                    if rid == "dummy-page":
                        if related_page_ids:
                            if related_page_ids:
                                real_ids.append(related_page_ids.pop(0))
                    elif rid:
                        real_ids.append(rid)
                if real_ids:
                    props[key] = {"relation": [{"id": i} for i in real_ids]}
            else:
                if isinstance(value, list) and value and value[0].get("object") == "user":
                    people_ids = []
                    for person in value:
                        pid = person.get("id")
                        if pid == "dummy-user" and DEFAULT_USER_ID:
                            people_ids.append({"id": DEFAULT_USER_ID})
                        elif pid and pid != "dummy-user":
                            people_ids.append({"id": pid})
                    if people_ids:
                        props[key] = {"people": people_ids}
                elif isinstance(value, str):
                    props[key] = {"rich_text": [{"text": {"content": value}}]}
        res = notion.pages.create(parent={"database_id": db_id}, properties=props)
        page_ids.append(res.get("id", ""))
        if template_title == "회사 일정 캘린더" and "시작일" in props:
            create_event(
                props["제목"]["title"][0]["text"]["content"],
                props["시작일"]["date"]["start"],
                props.get("종료일", {"date": {"start": props["시작일"]["date"]["start"]}})["date"]["start"],
                item.get("설명", ""),
            )
    log.info("더미 데이터 %d건 삽입", len(items))
    return page_ids

def add_relation_columns(db_id_map: Dict[str, str]) -> None:
    """Update databases with relation properties once all IDs are known."""
    if not notion:
        log.debug("노션 클라이언트 미설정")
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
                        "관계 대상 %s(%s) 을 찾을 수 없습니다", target_title, name
                    )

        if updates:
            try:
                notion.databases.update(db_id, properties=updates)
                log.info("%s 데이터베이스의 relation 업데이트 완료", tmpl["template_title"])
            except Exception as exc:
                log.error("relation 업데이트 실패 %s: %s", db_id, exc)

# Example usage:
# db_id = create_database(templates.DATABASE_TEMPLATES[0])
# asyncio.run(create_dummy_data(db_id, "출장 요청서"))
