# 🚀 SaaS 운영 대시보드

스타트업 실무용 종합 업무 관리 템플릿입니다.  
기능 개발, 버그 관리, 고객 피드백, 회의록 등을 한 곳에서 통합 관리하세요.

---

## 🗂️ 주요 데이터베이스

### ✅ 업무 트래킹 DB (`Tasks`)

| 속성 이름     | 타입       | 설명                           |
|---------------|------------|--------------------------------|
| 📝 이슈 제목   | 제목       | 업무 항목 제목                  |
| 📌 상태       | 선택       | 할 일 / 진행 중 / 완료 / 보류 |
| 🔥 우선순위   | 선택       | 높음 / 보통 / 낮음             |
| 👤 담당자     | 사람       | 해당 업무 담당자                |
| 📅 마감일     | 날짜       | 업무 마감 기한                 |
| 🧩 카테고리   | 선택       | 기능 개발 / 버그 / 피드백 등  |
| 🏷️ 태그       | 멀티 선택  | 업무 키워드                    |
| 📄 설명       | 텍스트     | 상세 설명 또는 참고 링크        |
| 🔗 회의 연동  | 관계형     | 회의록 DB 항목 연결             |

---

### 🧩 보기 구성

- **보드 보기**: `상태`별 업무 흐름 정리 (칸반 보드 형태)
- **캘린더 보기**: `마감일` 기준 일정 시각화
- **갤러리 보기**: 팀별/기능별 분류 후 카드형 UI
- **표 보기**: 전체 업무 목록 + 필터 기능

---

## 💬 회의록 DB (`Meetings`)

| 속성         | 타입      | 설명                         |
|--------------|-----------|------------------------------|
| 📅 회의 일자  | 날짜      | 회의 날짜                    |
| 📝 주제       | 제목      | 회의 제목                    |
| 👥 참석자     | 사람      | 회의 참가자 목록             |
| 🗒️ 주요 논의 | 텍스트    | 요점 정리                    |
| 🏷️ 태그       | 멀티 선택 | 프로젝트/기능명 등 분류 태그 |

---

## 🧠 고객 피드백 DB (`Feedback`)

| 속성         | 타입       | 설명                          |
|--------------|------------|-------------------------------|
| 💬 요청 제목  | 제목       | 고객 요청 요약                 |
| 🏢 고객사     | 텍스트     | 고객사 이름                    |
| 📅 요청일     | 날짜       | 요청 접수 일자                 |
| 🔥 중요도     | 선택       | 높음 / 보통 / 낮음             |
| 🧩 연관 기능  | 선택       | 해당 요청과 연관된 기능         |
| 🔗 업무 연동  | 관계형     | 관련 업무 DB 항목과 연결        |

---

## 🤖 Notion API 자동화 (Python 예시)

```python
from notion_client import Client

notion = Client(auth="your-secret-token")

database_id = "your-db-id"

new_task = {
    "parent": { "database_id": database_id },
    "properties": {
        "이슈 제목": {
            "title": [{ "text": { "content": "신규 기능: 구독 리포트 생성" } }]
        },
        "상태": { "select": { "name": "할 일" } },
        "우선순위": { "select": { "name": "높음" } },
        "담당자": {
            "people": [{ "object": "user", "id": "user-id" }]
        },
        "마감일": {
            "date": { "start": "2025-06-20" }
        }
    }
}

notion.pages.create(**new_task)
```

---

## 🔔 Slack 연동 예시

```python
import requests

SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/XXX/YYY/ZZZ"

def send_notion_update_to_slack(task_title, due_date):
    message = {
        "text": f"📢 새로운 업무 등록됨: *{task_title}*\n🗓 마감일: {due_date}"
    }
    requests.post(SLACK_WEBHOOK_URL, json=message)

send_notion_update_to_slack("신규 기능: 리포트 생성", "2025-06-20")
```

