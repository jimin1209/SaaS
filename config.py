"""Configuration loader for environment variables and constants."""
import os
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - allow tests without dependency
    def load_dotenv(*args, **kwargs):
        return False

# Load environment variables from .env file if present
load_dotenv()

# Notion credentials
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
PARENT_PAGE_ID = os.getenv("PARENT_PAGE_ID")

# Slack settings
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#general")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_ERROR_WEBHOOK_URL = os.getenv("SLACK_ERROR_WEBHOOK_URL")

# Google calendar (optional)
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE")
GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Example usage:
# from config import NOTION_TOKEN
