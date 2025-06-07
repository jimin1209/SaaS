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
3. Edit `.env` with your tokens and IDs. `SLACK_WEBHOOK_URL`에 에러 알림용 웹훅 주소를 설정하세요.
   If `NOTION_TOKEN` is not provided the script logs a warning and exits
   without touching Notion, which is useful for CI runs.
4. Relation columns can specify a `target_template` value. Databases are
   created first and then these relations are automatically added in a second
   step once the target database IDs are known.
5. Every database is checked right after creation to ensure a ``상태`` status
   column exists. If it is missing or of a wrong type it will be automatically
   added so subsequent operations work reliably.

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
