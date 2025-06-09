"""Google Calendar integration helpers."""
try:
    from googleapiclient.discovery import build
    from google.oauth2.service_account import Credentials
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    build = None
    Credentials = None
from config import GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_ID
from logging_utils import get_logger

log = get_logger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]
_service = None
if GOOGLE_CREDENTIALS_FILE and Credentials and build:
    try:
        creds = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
        )
        _service = build("calendar", "v3", credentials=creds)
    except Exception as exc:  # pragma: no cover - filesystem/network issues
        log.error("구글 캘린더 서비스 초기화 실패: %s", exc)
else:  # pragma: no cover - optional dependency
    log.debug("GOOGLE_CREDENTIALS_FILE 미설정")


def create_event(summary: str, start: str, end: str, description: str = "") -> None:
    """Create a calendar event using RFC3339 date strings."""
    if not _service:
        log.debug("구글 캘린더 서비스 사용 불가")
        return
    event = {
        "summary": summary,
        "start": {"date": start},
        "end": {"date": end},
    }
    if description:
        event["description"] = description
    try:
        _service.events().insert(calendarId=GOOGLE_CALENDAR_ID, body=event).execute()
        log.info("캘린더 이벤트 생성: %s", summary)
    except Exception as exc:  # pragma: no cover - network issues
        log.error("캘린더 이벤트 생성 실패 %s: %s", summary, exc)


def update_event(
    event_id: str,
    *,
    summary: str | None = None,
    start: str | None = None,
    end: str | None = None,
    description: str | None = None,
) -> None:
    """Update an existing calendar event."""
    if not _service:
        log.debug("구글 캘린더 서비스 사용 불가")
        return
    body: dict = {}
    if summary:
        body["summary"] = summary
    if start:
        body.setdefault("start", {})["date"] = start
    if end:
        body.setdefault("end", {})["date"] = end
    if description is not None:
        body["description"] = description
    try:
        _service.events().patch(
            calendarId=GOOGLE_CALENDAR_ID, eventId=event_id, body=body
        ).execute()
        log.info("캘린더 이벤트 업데이트: %s", event_id)
    except Exception as exc:  # pragma: no cover - network issues
        log.error("캘린더 이벤트 업데이트 실패 %s: %s", event_id, exc)
