"""Configuration from environment variables."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Bot token
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not set in .env", file=sys.stderr)
    sys.exit(1)

# Archive chat ID for storing uploaded videos
ARCHIVE_CHAT_ID_STR = os.getenv("ARCHIVE_CHAT_ID")
if not ARCHIVE_CHAT_ID_STR:
    print("ERROR: ARCHIVE_CHAT_ID not set in .env", file=sys.stderr)
    sys.exit(1)

try:
    ARCHIVE_CHAT_ID = int(ARCHIVE_CHAT_ID_STR)
except ValueError:
    print(f"ERROR: ARCHIVE_CHAT_ID must be integer, got '{ARCHIVE_CHAT_ID_STR}'", file=sys.stderr)
    sys.exit(1)

# Logging level
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL not in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    print(f"WARNING: Invalid LOG_LEVEL '{LOG_LEVEL}', using INFO", file=sys.stderr)
    LOG_LEVEL = "INFO"

# Cache TTL in seconds
try:
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
except ValueError:
    print("WARNING: Invalid CACHE_TTL, using 3600", file=sys.stderr)
    CACHE_TTL = 3600

# File size limits
MAX_FILESIZE_MB = 50
MAX_FILESIZE_BYTES = MAX_FILESIZE_MB * 1024 * 1024
PRE_CHECK_LIMIT_MB = 45  # Safety margin for container overhead
PRE_CHECK_LIMIT_BYTES = PRE_CHECK_LIMIT_MB * 1024 * 1024

# yt-dlp estimated bitrate for videos without filesize metadata (bytes/sec)
ESTIMATED_BITRATE = 150_000  # ~1.2 Mbit/s

# Telegram inline query timeout (seconds)
INLINE_TIMEOUT = 25

# Supported domains regex patterns
SUPPORTED_DOMAINS = [
    r"(?:https?://)?(?:www\.)?tiktok\.com/[^\s]+",
    r"(?:https?://)?(?:www\.)?(?:youtube\.com/shorts|youtu\.be)/[^\s]+",
]

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
