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
        log.error("Failed to init Google Calendar service: %s", exc)
else:  # pragma: no cover - optional dependency
    log.debug("GOOGLE_CREDENTIALS_FILE not configured")


def create_event(summary: str, start: str, end: str, description: str = "") -> None:
    """Create a calendar event using RFC3339 date strings."""
    if not _service:
        log.debug("Google Calendar service not available")
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
        log.info("Created calendar event %s", summary)
    except Exception as exc:  # pragma: no cover - network issues
        log.error("Failed to create calendar event %s: %s", summary, exc)
