"""
config.py
-----------
Central configuration for the AI Resume Analyzer & Career Assistant.
All environment-driven and constant settings live here so app.py and
utils.py never hard-code values.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load variables from .env into the process environment
load_dotenv()

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Base Flask configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"

    # Database
    DATABASE_PATH = str(BASE_DIR / "database.db")

    # Uploads
    UPLOAD_FOLDER = str(BASE_DIR / "uploads")
    ALLOWED_EXTENSIONS = {"pdf"}
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload size

    # Gemini AI
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Misc
    APP_NAME = "AI Resume Analyzer & Career Assistant"


def ensure_directories():
    """Create required runtime directories if they do not already exist."""
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
