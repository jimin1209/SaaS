import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import calendar_sync
from unittest.mock import MagicMock, patch


def test_sync_notion_calendar_creates_events():
    pages = {
        "results": [
            {
                "properties": {
                    "제목": {"title": [{"text": {"content": "회의"}}]},
                    "시작일": {"date": {"start": "2024-10-01"}},
                    "종료일": {"date": {"start": "2024-10-02"}},
                    "설명": {"rich_text": [{"text": {"content": "내용"}}]},
                }
            }
        ],
        "next_cursor": None,
    }

    with patch("calendar_sync.notion") as notion, patch(
        "calendar_sync.create_event"
    ) as create:
        notion.databases.query.return_value = pages
        calendar_sync.sync_notion_calendar("db")
        create.assert_called_once_with(
            "회의", "2024-10-01", "2024-10-02", "내용"
        )
