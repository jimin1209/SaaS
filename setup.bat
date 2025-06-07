@echo off
REM Activate virtual environment and run SaaS

if not exist venv (
    python -m venv venv
)

call venv\Scripts\activate
pip install -r requirements.txt

if not exist .env (
    copy .env.example .env
)

python SaaS.py
pause

