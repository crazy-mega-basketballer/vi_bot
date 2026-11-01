"""Simple in-memory TTL cache for file_id."""

import time
from typing import Optional


class FileCache:
    """Thread-safe in-memory cache with TTL."""

    def __init__(self, ttl: int) -> None:
        """Initialize cache with TTL in seconds."""
        self.ttl = ttl
        self._cache: dict[str, tuple[str, float]] = {}

    def get(self, key: str) -> Optional[str]:
        """Get file_id from cache if not expired."""
        if key not in self._cache:
            return None

        file_id, expires_at = self._cache[key]
        if time.time() > expires_at:
            del self._cache[key]
            return None

        return file_id

    def set(self, key: str, file_id: str) -> None:
        """Store file_id with TTL."""
        expires_at = time.time() + self.ttl
        self._cache[key] = (file_id, expires_at)

    def clear_expired(self) -> None:
        """Remove all expired entries (optional cleanup)."""
        now = time.time()
        expired_keys = [k for k, (_, exp) in self._cache.items() if now > exp]
        for key in expired_keys:
            del self._cache[key]
