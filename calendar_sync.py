"""Helpers to sync Notion calendar databases with Google Calendar."""
from logging_utils import get_logger
from notion_db_utils import notion
from google_calendar_utils import create_event

log = get_logger(__name__)


def _get_plain_text(prop: dict) -> str:
    """Extract plain text from a Notion rich text or title property."""
    texts = []
    for t in prop.get("rich_text") or prop.get("title") or []:
        if "plain_text" in t:
            texts.append(t["plain_text"])
        elif t.get("text"):
            texts.append(t["text"].get("content", ""))
    return "".join(texts)


def sync_notion_calendar(db_id: str) -> None:
    """Create calendar events for all rows in the given Notion database."""
    if not notion:
        log.debug("노션 클라이언트 미설정")
        return
    cursor = None
    try:
        while True:
            if cursor:
                data = notion.databases.query(db_id, start_cursor=cursor)
            else:
                data = notion.databases.query(db_id)
            for page in data.get("results", []):
                props = page.get("properties", {})
                title = _get_plain_text(props.get("제목", {})) or "Untitled"
                start = props.get("시작일", {}).get("date", {}).get("start")
                end = props.get("종료일", {}).get("date", {}).get("start", start)
                desc = _get_plain_text(props.get("설명", {}))
                if start:
                    create_event(title, start, end, desc)
            cursor = data.get("next_cursor")
            if not cursor:
                break
    except Exception as exc:
        log.error("캘린더 동기화 실패: %s", exc)
