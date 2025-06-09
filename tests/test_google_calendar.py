import google_calendar_utils as gcal
from unittest.mock import MagicMock, patch


def test_create_event_calls_api():
    with patch.object(gcal, "_service") as svc:
        events = MagicMock()
        svc.events.return_value = MagicMock(insert=MagicMock(return_value=MagicMock(execute=MagicMock())))
        gcal.create_event("회의", "2024-10-01", "2024-10-01", "desc")
        svc.events.assert_called_once()


def test_update_event_calls_api():
    with patch.object(gcal, "_service") as svc:
        svc.events.return_value = MagicMock(patch=MagicMock(return_value=MagicMock(execute=MagicMock())))
        gcal.update_event("eid", summary="회의")
        svc.events.assert_called_once()

