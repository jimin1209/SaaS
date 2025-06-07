# SaaS Automation

This project automates creation of Notion databases and posts status messages to Slack.
It has been organised into small reusable modules for easy maintenance.

## Folder Structure
```
/.github/workflows - CI/CD pipeline
/tests             - pytest tests
config.py          - environment variables loader
logging_utils.py   - logging helpers
notion_db_utils.py - Notion database functions
notion_templates.py- DB templates and dummy data
slack_utils.py     - Slack notification helpers
main.py            - entry point using the above modules
.env.example       - environment variable template
```

## Quick Start (Windows)
1. Clone the repository and open a VSCode terminal.
2. Run `setup.bat` which creates `venv`, installs dependencies and executes `main.py`.
3. Edit `.env` with your tokens and IDs. `SLACK_WEBHOOK_URL`과
   `SLACK_ERROR_WEBHOOK_URL`에 각각 기본 로그용과 에러 알림용 웹훅 주소를 설정하세요.
   If `NOTION_TOKEN` is not provided the script logs a warning and exits
   without touching Notion, which is useful for CI runs.
4. Relation columns can specify a `target_template` value. Databases are
   created first and then these relations are automatically added in a second
   step once the target database IDs are known.
5. Every database is checked right after creation to ensure a ``상태`` select
   column exists. If it is missing or of a wrong type it will be automatically
   added so subsequent operations work reliably. The column is created with
   기본 상태값 *미처리/진행중/완료/반려*와 색상이 설정되며 원하는 기본값을
   함수 인자로 지정할 수 있습니다.
   
  TODO: 실제 결과 화면을 캡처해 `docs/` 폴더에 저장한 뒤 위 링크로
  이미지 경로를 업데이트하세요.

## Slack 로그 연동
`SlackLogHandler`가 모든 로그를 슬랙 웹훅으로 전송합니다. 일반 로그는
`SLACK_WEBHOOK_URL`을, 에러 로그는 `SLACK_ERROR_WEBHOOK_URL`을 사용합니다.
다음과 같이 핸들러를 설정합니다:

```python
from slack_utils import SlackLogHandler
import logging

root_logger = logging.getLogger()
root_logger.addHandler(SlackLogHandler())
```

이후 `logging.info()` 등으로 기록한 메시지는 실시간으로 슬랙에서 확인할 수
있습니다.

## Google Calendar 연동
`google_calendar_utils.create_event` 함수는 서비스 계정 키(`GOOGLE_CREDENTIALS_FILE`)
와 캘린더 ID(`GOOGLE_CALENDAR_ID`)를 사용해 이벤트를 등록합니다. `main.py`에서는
"회사 일정 캘린더" 데이터베이스에 더미 데이터를 넣을 때 자동으로 일정이 생성됩니다.

```python
from google_calendar_utils import create_event

create_event("회의", "2024-10-01", "2024-10-01", "월간 회의")
```

실행 후 구글 캘린더에서 이벤트가 정상적으로 생성됐는지 확인하세요.

## Running as Windows Service
1. Install [nssm](https://nssm.cc/).
2. Register the service:
   ```cmd
   nssm install SaaSService "C:\path\to\venv\Scripts\python.exe" "C:\repo\main.py"
   ```
3. Start the service via `nssm start SaaSService`.

## GitHub Actions
`deploy.yml` runs the script on every push to `main`. Secrets for tokens and the Google service account JSON should be stored in the repository secrets.

## Tests
Run `pytest` to execute the unit tests.

## 확장/수정 가이드
* 상태 옵션을 변경하려면 ``notion_db_utils.py`` 상단의 ``DEFAULT_SELECT_OPTIONS``
  리스트를 수정하세요.
* 기본 상태값을 바꾸려면 ``DEFAULT_SELECT_NAME`` 상수를 변경하거나
  ``ensure_status_column`` 호출 시 ``default_name`` 인자를 전달하면 됩니다.
* 더미 데이터 삽입 시 각 템플릿의 속성 정의에 맞춰 타입을 자동 매핑하므로
  ``부서 is expected to be select`` 와 같은 오류를 방지합니다.
* Notion API 구조가 변경되면 함수 내부의 ``select_cfg`` 빌드 부분을
  업데이트 하면 대부분의 코드 수정 없이 동작을 맞출 수 있습니다.
* 기본적으로 Notion의 ``status`` 속성은 고정된 상태 그룹을 제공하지만 이
  예제에서는 API 호환성을 위해 ``select`` 타입으로 동일한 옵션을 구성하고
  있습니다. 필요 시 ``ensure_status_column`` 내부 코드를 수정해 다른 방식도
  적용할 수 있습니다.
