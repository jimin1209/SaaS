# -*- coding: utf-8 -*-

from notion_client import Client
import copy
import time
import asyncio
import aiohttp
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# 환경설정
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL")
GOOGLE_CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "titanium-web-461107-a4-b2f324177ba1.json")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

notion = Client(auth=NOTION_TOKEN)
slack_client = AsyncWebClient(token=SLACK_BOT_TOKEN)

def init_google_calendar():
    try:
        creds = service_account.Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        service = build('calendar', 'v3', credentials=creds)
        print("[Google Calendar] 초기화 성공")
        return service
    except Exception as e:
        print(f"[Google Calendar] 초기화 실패: {e}")
        return None

google_calendar_service = init_google_calendar()

def delete_existing_databases():
    print("== 기존 DB 전체 삭제 시도 ==")
    try:
        children = notion.blocks.children.list(PARENT_PAGE_ID).get("results", [])
        for block in children:
            if block["type"] == "child_database":
                try:
                    notion.blocks.delete(block_id=block["id"])
                    print(f"🗑️ 기존 DB 삭제됨 → {block['id']}")
                except Exception as e:
                    print(f"❌ 삭제 실패: {e}")
        print("== 기존 DB 삭제 완료 ==")
    except Exception as e:
        print(f"기존 DB 삭제 중 오류: {e}")
        print("PARENT_PAGE_ID가 올바르고, 통합이 공유되었는지 확인하세요.")

databases_to_create = [
    {
        "template_title": "📥 지출결의서",
        "icon_emoji": "📥",
        "properties": {
            "제목": {"title": {}},
            "항목명": {"rich_text": {}},
            "금액": {"number": {"format": "number"}},
            "계정과목": {"select": {}},
            "요청일": {"date": {}},
            "요청월": {"select": {}},
            "요청자": {"people": {}},
            "상태": {"status": {}},
            "첨부파일": {"files": {}},
        },
    },
    {
        "template_title": "✈️ 출장 요청서",
        "icon_emoji": "✈️",
        "properties": {
            "제목": {"title": {}},
            "출장자": {"people": {}},
            "출장지": {"rich_text": {}},
            "출장기간": {"date": {}},
            "출장목적": {"rich_text": {}},
            "상태": {"status": {}},
        },
    },
    {
        "template_title": "🌴 휴가 기록서",
        "icon_emoji": "🌴",
        "properties": {
            "제목": {"title": {}},
            "휴가자": {"people": {}},
            "휴가시작": {"date": {}},
            "휴가종료": {"date": {}},
            "휴가유형": {"select": {}},
            "상태": {"status": {}},
        },
    },
    {
        "template_title": "📝 교육 수강 신청서",
        "icon_emoji": "📝",
        "properties": {
            "제목": {"title": {}},
            "수강생": {"people": {}},
            "교육명": {"rich_text": {}},
            "교육일": {"date": {}},
            "상태": {"status": {}},
        },
    },
    {
        "template_title": "👥 직원목록",
        "icon_emoji": "👥",
        "properties": {
            "제목": {"title": {}},
            "이름": {"rich_text": {}},
            "부서": {"select": {}},
            "직급": {"select": {}},
            "상태": {"status": {}},
        },
    },
    {
        "template_title": "📅 회사 일정 캘린더",
        "icon_emoji": "📅",
        "properties": {
            "제목": {"title": {}},
            "시작일": {"date": {}},
            "종료일": {"date": {}},
            "상태": {"status": {}},
            "설명": {"rich_text": {}},
        },
    },
    {
        "template_title": "📁 휴가 및 출장 증빙서류",
        "icon_emoji": "📁",
        "properties": {
            "제목": {"title": {}},
            "관련 요청": {"relation": {}},
            "첨부파일": {"files": {}},
            "상태": {"status": {}},
        },
    },
]

async def create_database_and_postprocess(template):
    try:
        db = copy.deepcopy(template)
        title_text = db.pop("template_title")
        icon_emoji = db.pop("icon_emoji", "📄")
        title_format = [{"type": "text", "text": {"content": title_text}}]

        print(f"\n=== [{title_text}] DB 생성 요청 ===")
        result = notion.databases.create(
            parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
            title=title_format,
            icon={"type": "emoji", "emoji": icon_emoji},
            properties=db["properties"],
        )
        db_id = result["id"]
        print(f"  - [{title_text}] DB 생성 완료 → DB ID: {db_id}")

        prop = notion.databases.retrieve(db_id)["properties"].get("상태")
        if not prop or prop.get("type") != "status":
            print(f"  - [{title_text}] 상태 컬럼이 없거나 status 타입 아님, 재설정 시도")
            notion.databases.update(db_id, properties={"상태": {"status": {}}})
            print(f"  - [{title_text}] 상태 컬럼을 status 타입으로 추가 완료!")
        else:
            print(f"  - [{title_text}] 상태 컬럼 타입 확인 완료")

        if "관련 요청" in db["properties"]:
            try:
                notion.databases.update(
                    db_id,
                    properties={
                        "관련 요청": {
                            "relation": {
                                "database_id": None,
                                "single_property": "제목",
                            }
                        }
                    },
                )
            except Exception as e:
                print(f"  - [{title_text}] 관련 요청 Relation 업데이트 실패: {e}")

        try:
            notion.pages.create(
                parent={"database_id": db_id},
                properties={"제목": {"title": [{"type": "text", "text": {"content": "📄 자동 생성된 첫 요청"}}]}},
            )
            print(f"▶ [{title_text}] 첫 요청(더미) 페이지 생성 시작")
        except Exception as e:
            print(f"  - [{title_text}] 더미 요청 생성 실패(예외처리): {e}")

        return db_id
    except Exception as e:
        print(f"[{template.get('template_title', '알 수 없음')}] DB 생성 실패: {e}")
        return None

async def create_dummy_data(db_id, template_title):
    print(f"▶ [{template_title}] 더미 데이터 5건 추가 시작")

    dummy_items_map = {
        "📥 지출결의서": [
            {"제목": "지출1", "항목명": "노트북", "금액": 1500000, "계정과목": "소모품비", "요청일": "2024-05-01", "요청월": "2024-05", "요청자": [], "상태": "미처리"},
            {"제목": "지출2", "항목명": "모니터", "금액": 300000, "계정과목": "기타", "요청일": "2024-05-05", "요청월": "2024-05", "요청자": [], "상태": "승인됨"},
            {"제목": "지출3", "항목명": "키보드", "금액": 100000, "계정과목": "소모품비", "요청일": "2024-05-10", "요청월": "2024-05", "요청자": [], "상태": "미처리"},
            {"제목": "지출4", "항목명": "마우스", "금액": 50000, "계정과목": "기타", "요청일": "2024-05-15", "요청월": "2024-05", "요청자": [], "상태": "승인됨"},
            {"제목": "지출5", "항목명": "책상", "금액": 250000, "계정과목": "복리후생", "요청일": "2024-05-20", "요청월": "2024-05", "요청자": [], "상태": "미처리"},
        ],
        "✈️ 출장 요청서": [
            {"제목": "출장1", "출장자": [], "출장지": "서울", "출장기간": "2024-06-01/2024-06-05", "출장목적": "회의", "상태": "진행중"},
            {"제목": "출장2", "출장자": [], "출장지": "부산", "출장기간": "2024-06-10/2024-06-12", "출장목적": "교육", "상태": "승인됨"},
            {"제목": "출장3", "출장자": [], "출장지": "대전", "출장기간": "2024-06-15/2024-06-18", "출장목적": "출장", "상태": "진행중"},
            {"제목": "출장4", "출장자": [], "출장지": "인천", "출장기간": "2024-06-20/2024-06-22", "출장목적": "미팅", "상태": "미처리"},
            {"제목": "출장5", "출장자": [], "출장지": "광주", "출장기간": "2024-06-25/2024-06-27", "출장목적": "회의", "상태": "진행중"},
        ],
        "🌴 휴가 기록서": [
            {"제목": "휴가1", "휴가자": [], "휴가시작": "2024-07-01", "휴가종료": "2024-07-05", "휴가유형": "연차", "상태": "승인됨"},
            {"제목": "휴가2", "휴가자": [], "휴가시작": "2024-07-10", "휴가종료": "2024-07-12", "휴가유형": "병가", "상태": "미처리"},
            {"제목": "휴가3", "휴가자": [], "휴가시작": "2024-07-15", "휴가종료": "2024-07-18", "휴가유형": "연차", "상태": "승인됨"},
            {"제목": "휴가4", "휴가자": [], "휴가시작": "2024-07-20", "휴가종료": "2024-07-22", "휴가유형": "병가", "상태": "미처리"},
            {"제목": "휴가5", "휴가자": [], "휴가시작": "2024-07-25", "휴가종료": "2024-07-28", "휴가유형": "연차", "상태": "승인됨"},
        ],
        "📝 교육 수강 신청서": [
            {"제목": "교육1", "수강생": [], "교육명": "파이썬 기초", "교육일": "2024-08-01", "상태": "승인됨"},
            {"제목": "교육2", "수강생": [], "교육명": "데이터 분석", "교육일": "2024-08-05", "상태": "미처리"},
            {"제목": "교육3", "수강생": [], "교육명": "머신러닝", "교육일": "2024-08-10", "상태": "승인됨"},
            {"제목": "교육4", "수강생": [], "교육명": "인공지능", "교육일": "2024-08-15", "상태": "미처리"},
            {"제목": "교육5", "수강생": [], "교육명": "빅데이터", "교육일": "2024-08-20", "상태": "승인됨"},
        ],
        "👥 직원목록": [
            {"제목": "직원1", "이름": "홍길동", "부서": "개발팀", "직급": "사원", "상태": "재직"},
            {"제목": "직원2", "이름": "김철수", "부서": "영업팀", "직급": "대리", "상태": "재직"},
            {"제목": "직원3", "이름": "이영희", "부서": "기획팀", "직급": "과장", "상태": "퇴사"},
            {"제목": "직원4", "이름": "박민수", "부서": "개발팀", "직급": "대리", "상태": "재직"},
            {"제목": "직원5", "이름": "최지민", "부서": "기획팀", "직급": "사원", "상태": "재직"},
        ],
        "📅 회사 일정 캘린더": [
            {"제목": "회의1", "시작일": "2024-09-01", "종료일": "2024-09-01", "상태": "예정", "설명": "월간 회의"},
            {"제목": "교육1", "시작일": "2024-09-05", "종료일": "2024-09-05", "상태": "진행중", "설명": "신규 교육"},
            {"제목": "회의2", "시작일": "2024-09-10", "종료일": "2024-09-10", "상태": "예정", "설명": "전사 회의"},
            {"제목": "휴가", "시작일": "2024-09-15", "종료일": "2024-09-20", "상태": "진행중", "설명": "휴가 기간"},
            {"제목": "워크샵", "시작일": "2024-09-25", "종료일": "2024-09-27", "상태": "예정", "설명": "팀 워크샵"},
        ],
        "📁 휴가 및 출장 증빙서류": [
            # 증빙서류 더미 데이터는 생략
        ],
    }

    dummy_items = dummy_items_map.get(template_title, [])
    count = 0
    for item in dummy_items:
        count += 1
        props = {}
        for key, value in item.items():
            if key == "제목":
                props["제목"] = {"title": [{"text": {"content": value}}]}
            elif key in ("항목명", "출장지", "출장목적", "교육명", "이름", "설명"):
                props[key] = {"rich_text": [{"text": {"content": value}}]}
            elif key == "금액":
                props[key] = {"number": value}
            elif key in ("계정과목", "부서", "직급", "휴가유형", "요청월"):
                props[key] = {"select": {"name": value}}
            elif key == "상태":
                props[key] = {"status": {"name": value}}
            elif key in ("출장자", "휴가자", "수강생"):
                props[key] = {"people": value if isinstance(value, list) else []}
            elif key in ("요청일", "출장기간", "휴가시작", "휴가종료", "교육일", "시작일", "종료일"):
                if isinstance(value, str) and "/" in value:
                    start, end = value.split("/")
                    props[key] = {"date": {"start": start, "end": end}}
                else:
                    props[key] = {"date": {"start": value}}
            else:
                props[key] = {"rich_text": [{"text": {"content": str(value)}}]}
        try:
            notion.pages.create(parent={"database_id": db_id}, properties=props)
        except Exception as e:
            print(f"  - [{template_title}] 더미 데이터 {count} 생성 실패: {e}")

    print(f"▶ [{template_title}] 더미 데이터 {count}건 추가 완료")

async def main_async():
    delete_existing_databases()

    db_ids = []
    tasks = []
    for template in databases_to_create:
        tasks.append(create_database_and_postprocess(template))
    results = await asyncio.gather(*tasks)
    db_ids = [r for r in results if r]

    for db_id, template in zip(db_ids, databases_to_create):
        await create_dummy_data(db_id, template["template_title"])

    print("\n== 모든 DB 생성 및 후처리 완료 ==")
    print(f"생성된 DB ID 리스트: {db_ids}")

    try:
        await slack_client.chat_postMessage(
            channel=SLACK_CHANNEL,
            text="✅ Notion DB 자동화 및 더미 데이터 생성이 완료되었습니다!"
        )
        print(f"[슬랙] '{SLACK_CHANNEL}' 채널에 메시지 전송 완료.")
    except SlackApiError as e:
        print(f"[슬랙] 메시지 전송 실패: {e.response['error']}")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
