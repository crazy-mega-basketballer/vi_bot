"""URL extraction and normalization."""

import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

from bot.config import SUPPORTED_DOMAINS


def extract_url(text: str) -> Optional[str]:
    """Extract first supported URL from text."""
    for pattern in SUPPORTED_DOMAINS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def normalize_url(url: str) -> str:
    """Normalize URL for cache key (remove query params, fragments)."""
    # Ensure scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)
    # Keep only scheme, netloc, path
    normalized = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return normalized.lower()


def get_platform_name(url: str) -> str:
    """Get human-readable platform name from URL."""
    if "tiktok.com" in url.lower():
        return "TikTok"
    if "youtube.com" in url.lower() or "youtu.be" in url.lower():
        return "YouTube Shorts"
    return "видео"
