"""
Configuration settings for Suno API Client
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DOWNLOADS_DIR = BASE_DIR / "downloads"

# API Configuration
API_BASE_URL = "https://api.sunoapi.org"
API_VERSION = "v1"

# Default settings
DEFAULT_MODEL = "V4_5"
DEFAULT_TIMEOUT = 600  # 10 minutes max wait time
POLL_INTERVAL = 30  # seconds between status checks

# Available models
AVAILABLE_MODELS = ["V3_5", "V4", "V4_5", "V4_5PLUS", "V5"]

# Task statuses
TASK_STATUS = {
    "PENDING": "Queued for processing",
    "GENERATING": "Being processed",
    "SUCCESS": "Completed successfully",
    "FAILED": "Failed to complete"
}


def get_api_key() -> str:
    """Load API key from key.txt file"""
    key_file = BASE_DIR / "key.txt"
    
    if not key_file.exists():
        raise FileNotFoundError(f"API key file not found: {key_file}")
    
    # Try different encodings
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
        try:
            api_key = key_file.read_text(encoding=encoding).strip()
            if api_key:
                return api_key
        except UnicodeDecodeError:
            continue
    
    raise ValueError("API key file is empty or unreadable")


def ensure_downloads_dir() -> Path:
    """Ensure downloads directory exists and return its path"""
    DOWNLOADS_DIR.mkdir(exist_ok=True)
    return DOWNLOADS_DIR
