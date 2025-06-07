# SaaS Automation

This project automates creation of Notion databases and posts status messages to Slack. A Google Calendar integration example is also included.

## Folder Structure
```
/.github/workflows  - CI/CD pipeline
/tests               - pytest tests
setup.bat            - Windows setup helper
SaaS.py              - main automation script
.env.example         - environment variable template
```

## Quick Start (Windows)
1. Clone the repository and open a VSCode terminal.
2. Run `setup.bat`. The script creates/activates `venv`, installs dependencies, copies `.env.example` to `.env` if missing and executes `SaaS.py`.
3. Edit `.env` with your tokens and IDs.

## Running as Windows Service
1. Install [nssm](https://nssm.cc/).
2. Register the service:
   ```cmd
   nssm install SaaSService "C:\path\to\venv\Scripts\python.exe" "C:\repo\SaaS.py"
   ```
3. Start the service via `nssm start SaaSService`.

## GitHub Actions
`deploy.yml` runs the script on every push to `main`. Secrets for tokens and the Google service account JSON should be stored in the repository secrets.

## Tests
Run `pytest` to execute the unit tests.

