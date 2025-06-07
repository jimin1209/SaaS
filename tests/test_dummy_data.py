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
        mock_notion.pages.create = MagicMock(return_value={"id": "p"})
        mock_notion.databases.retrieve.return_value = {
            "properties": {"상태": {"type": "select"}}
        }

        ids = await db_utils.create_dummy_data("db_id", "출장 요청서")

        assert mock_notion.pages.create.call_count == 5
        assert len(ids) == 5
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


def test_ensure_status_column_creates_missing():
    """상태 컬럼이 없을 때 자동으로 추가되는지 확인"""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.databases.retrieve.return_value = {"properties": {}}
        mock_notion.databases.update = MagicMock()

        db_utils.ensure_status_column("db1")

        call_args = mock_notion.databases.update.call_args
        assert call_args[0][0] == "db1"
        status_prop = call_args[1]["properties"]["상태"]["select"]
        names = [o["name"] for o in status_prop["options"]]
        assert names == ["미처리", "진행중", "완료", "반려"]
        assert status_prop["default"]["name"] == "미처리"


def test_ensure_status_column_skips_when_exists():
    """상태 컬럼이 이미 존재하면 수정하지 않아야 한다."""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.databases.retrieve.return_value = {
            "properties": {"상태": {"type": "select"}}
        }
        mock_notion.databases.update = MagicMock()

        db_utils.ensure_status_column("db1")

        mock_notion.databases.update.assert_not_called()


def test_ensure_status_column_updates_wrong_type():
    """속성 타입이 다른 경우 새로 생성되어야 한다."""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.databases.retrieve.return_value = {
            "properties": {"상태": {"type": "rich_text"}}
        }
        mock_notion.databases.update = MagicMock()

        db_utils.ensure_status_column("db2", default_name="완료")

        call_args = mock_notion.databases.update.call_args
        status_prop = call_args[1]["properties"]["상태"]["select"]
        assert status_prop["default"]["name"] == "완료"

@pytest.mark.asyncio
async def test_create_dummy_data_select_and_relation():
    """select 및 relation 타입이 올바르게 매핑되는지 확인"""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.pages.create = MagicMock(return_value={"id": "r"})
        mock_notion.databases.retrieve.return_value = {
            "properties": {"상태": {"type": "select"}}
        }

        await db_utils.create_dummy_data(
            "db",
            "휴가 및 출장 증빙서류",
            related_page_ids=["target"]
        )

        call = mock_notion.pages.create.call_args_list[0]
        props = call.kwargs["properties"]
        assert "관련 요청" in props
        assert props["관련 요청"]["relation"] == [{"id": "target"}]


@pytest.mark.asyncio
async def test_create_dummy_data_select_columns():
    """select 타입 컬럼이 문자열 값으로 생성되는지 확인"""

    with patch.object(db_utils, "notion") as mock_notion:
        mock_notion.pages.create = MagicMock(return_value={"id": "c"})
        mock_notion.databases.retrieve.return_value = {
            "properties": {"상태": {"type": "select"}}
        }

        await db_utils.create_dummy_data("db", "직원목록")

        props = mock_notion.pages.create.call_args_list[0].kwargs["properties"]
        assert props["부서"]["select"]["name"] == "개발팀"
        assert props["직급"]["select"]["name"] == "사원"

@pytest.mark.asyncio
async def test_create_dummy_data_replaces_dummy_user():
    """사람 속성의 dummy-user 값이 기본 사용자 ID로 대체되는지 확인"""

    with patch.object(db_utils, "notion") as mock_notion, patch.object(
        db_utils, "DEFAULT_USER_ID", "user-uuid"
    ):
        mock_notion.pages.create = MagicMock(return_value={"id": "p"})
        mock_notion.databases.retrieve.return_value = {
            "properties": {"상태": {"type": "select"}}
        }

        await db_utils.create_dummy_data("db", "지출결의서")

        props = mock_notion.pages.create.call_args_list[0].kwargs["properties"]
        assert props["요청자"]["people"] == [{"id": "user-uuid"}]
