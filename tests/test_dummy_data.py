import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import MagicMock, patch
import notion_db_utils as db_utils
import pytest

@pytest.mark.asyncio
async def test_trip_date_parsing():
    """출장 요청 더미 데이터 생성 시 날짜 파싱 검증"""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.pages.create = MagicMock()
        mock_notion.databases.retrieve.return_value = {
            "properties": {"상태": {"type": "status"}}
        }

        await db_utils.create_dummy_data("db_id", "출장 요청서")

        assert mock_notion.pages.create.call_count == 5
        first_call = mock_notion.pages.create.call_args_list[0]
        props = first_call.kwargs["properties"]
        assert props["출장기간"]["date"]["start"] == "2024-06-01"
        assert props["출장기간"]["date"]["end"] == "2024-06-05"


def test_add_relation_includes_single_property():
    """관계형 속성 업데이트 시 single_property 필드를 포함하는지 확인"""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.databases.update = MagicMock()

        db_utils.add_relation_columns({
            "휴가 및 출장 증빙서류": "db1",
            "출장 요청서": "db2",
        })

        call = mock_notion.databases.update.call_args_list[0]
        props = call.kwargs["properties"]["관련 요청"]["relation"]
        assert props["type"] == "single_property"
        assert props["single_property"] == {}


def test_delete_databases_handles_pagination():
    """모든 페이지를 순회하며 데이터베이스를 삭제하는지 테스트"""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.blocks.children.list.side_effect = [
            {
                "results": [{"id": "id1", "type": "child_database"}],
                "next_cursor": "c1",
            },
            {
                "results": [{"id": "id2", "type": "child_database"}],
                "next_cursor": None,
            },
        ]
        mock_notion.blocks.delete = MagicMock()

        db_utils.delete_existing_databases("parent")

        assert mock_notion.blocks.children.list.call_count == 2
        deleted = [c.kwargs["block_id"] for c in mock_notion.blocks.delete.call_args_list]
        assert deleted == ["id1", "id2"]
