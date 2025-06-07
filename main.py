"""Entry point that orchestrates the automation flow."""
import asyncio
import traceback
from logging_utils import get_logger
from slack_utils import send_message, send_error_webhook, SlackLogHandler
import logging
from config import LOG_LEVEL
from notion_db_utils import (
    delete_existing_databases,
    create_database,
    create_dummy_data,
    add_relation_columns,
    notion,
)
from notion_templates import DATABASE_TEMPLATES

root_logger = logging.getLogger()
root_logger.setLevel(LOG_LEVEL)
slack_handler = SlackLogHandler()
slack_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
root_logger.addHandler(slack_handler)
log = get_logger(__name__)


async def run() -> None:
    """Create Notion databases and fill them with sample data.

    ``create_database`` automatically verifies that a ``상태`` select column
    exists on each newly created database so that subsequent calls that rely on
    this field do not fail. 기본 옵션은 ``미처리/진행중/완료/반려``이며 필요한 경우
    ``ensure_status_column`` 호출 시 다른 기본값을 지정할 수 있습니다. 또한
    "회사 일정 캘린더" 테이블 더미 데이터는 생성과 동시에 구글 캘린더 일정도
    등록됩니다.
    """
    if not notion:
        log.warning("노션 클라이언트 미설정으로 생성을 건너뜁니다")
        await send_message("⚠️ 노션 인증 정보 없음")
        return
    delete_existing_databases()
    db_ids = {}
    for tmpl in DATABASE_TEMPLATES:
        db_id = create_database(tmpl)
        db_ids[tmpl["template_title"]] = db_id

    add_relation_columns(db_ids)

    page_ids = {}
    for tmpl in DATABASE_TEMPLATES:
        rel_ids = None
        if tmpl["template_title"] == "휴가 및 출장 증빙서류":
            rel_ids = page_ids.get("출장 요청서", []).copy()
        ids = await create_dummy_data(
            db_ids[tmpl["template_title"]],
            tmpl["template_title"],
            related_page_ids=rel_ids,
        )
        page_ids[tmpl["template_title"]] = ids
        
    await send_message("✅ Notion automation complete")


def main() -> None:
    try:
        asyncio.run(run())
    except Exception as exc:
        log.error("예상치 못한 오류: %s", exc)
        send_error_webhook(exc)
        raise


if __name__ == "__main__":
    main()
