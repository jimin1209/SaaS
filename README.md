# SaaS 자동화 예제

이 프로젝트는 노션 데이터베이스를 자동으로 생성하고 상태 메시지를 슬랙으로 전송하는 예제입니다.
각 기능을 모듈화하여 유지보수가 쉽도록 구성했습니다.

## 폴더 구조
```
/.github/workflows - CI/CD pipeline
/tests             - pytest 테스트
config.py          - 환경변수 로더
logging_utils.py   - 로깅 도우미
notion_db_utils.py - 노션 DB 관리 함수
notion_templates.py- DB 템플릿과 더미 데이터
slack_utils.py     - 슬랙 알림 모듈
main.py            - 실행 엔트리 포인트
.env.example       - 환경변수 예시 파일
```

## 빠른 시작(Windows)
1. 저장소를 클론한 뒤 VSCode 터미널을 엽니다.
2. `setup.bat`을 실행하면 가상환경을 만들고 의존성을 설치한 뒤 `main.py`를 실행합니다.
3. `.env` 파일에 토큰과 ID 값을 입력합니다. `SLACK_WEBHOOK_URL`과 `SLACK_ERROR_WEBHOOK_URL`에 각각 기본 로그용과 에러 알림용 웹훅 주소를 지정하세요.
   `NOTION_TOKEN`이 없으면 노션 작업을 건너뛰고 경고만 출력하므로 CI에서 유용합니다.
   사람 속성이 필요한 경우 `DEFAULT_USER_ID`에 사용할 노션 사용자 ID를 입력합니다. 없으면 해당 컬럼을 생략합니다.
4. 관계형 컬럼에는 `target_template` 값을 지정할 수 있습니다. 모든 데이터베이스를 생성한 뒤 이 정보를 사용해 관계를 자동으로 연결합니다.
5. 각 데이터베이스 생성 후 ``상태`` select 컬럼이 존재하는지 확인하며, 없거나 타입이 다르면 자동으로 추가합니다. 기본 옵션은 *미처리/진행중/완료/반려*이며 기본값은 함수 인자로 변경할 수 있습니다.
   
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

## 윈도우 서비스로 실행하기
1. [nssm](https://nssm.cc/)을 설치합니다.
2. 다음 명령으로 서비스를 등록합니다.
   ```cmd
   nssm install SaaSService "C:\path\to\venv\Scripts\python.exe" "C:\repo\main.py"
   ```
3. `nssm start SaaSService` 명령으로 서비스를 시작합니다.

## GitHub Actions
`deploy.yml` 워크플로우가 `main` 브랜치에 푸시될 때마다 스크립트를 실행합니다. 토큰과 구글 서비스 계정 JSON은 레포지토리 시크릿에 저장하세요.

## Tests
테스트는 `pytest` 명령으로 실행합니다.

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
