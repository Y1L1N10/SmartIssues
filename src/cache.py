"""Local cache management for SmartIssues."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class CacheEntry:
    """A single cache entry."""

    key: str
    value: Any
    created_at: float
    ttl: int

    def is_expired(self) -> bool:
        """Check if this entry has expired."""
        return time.time() > (self.created_at + self.ttl)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CacheEntry":
        """Create from dictionary."""
        return cls(
            key=data["key"],
            value=data["value"],
            created_at=data["created_at"],
            ttl=data["ttl"],
        )


class CacheManager:
    """Manage local file-based cache."""

    def __init__(self, cache_dir: Optional[Path] = None, default_ttl: int = 3600):
        """Initialize cache manager.

        Args:
            cache_dir: Directory for cache files
            default_ttl: Default time-to-live in seconds
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".smartissues" / "cache"

        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if needed."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get path for a cache key."""
        return self.cache_dir / f"{key}.json"

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        path = self._get_cache_path(key)

        if not path.exists():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                entry = CacheEntry.from_dict(data)

                if entry.is_expired():
                    self.delete(key)
                    return None

                return entry.value
        except (json.JSONDecodeError, KeyError):
            self.delete(key)
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        if ttl is None:
            ttl = self.default_ttl

        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            ttl=ttl,
        )

        path = self._get_cache_path(key)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(entry.to_dict(), f, indent=2, default=str)

    def delete(self, key: str) -> bool:
        """Delete a cache entry.

        Args:
            key: Cache key

        Returns:
            True if entry was deleted, False if not found
        """
        path = self._get_cache_path(key)
        if path.exists():
            path.unlink()
            return True
        return False

    def clear(self) -> int:
        """Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            count += 1
        return count

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries.

        Returns:
            Number of entries removed
        """
        count = 0
        for path in self.cache_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    entry = CacheEntry.from_dict(data)
                    if entry.is_expired():
                        path.unlink()
                        count += 1
            except (json.JSONDecodeError, KeyError):
                path.unlink()
                count += 1
        return count

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total = 0
        expired = 0
        total_size = 0

        for path in self.cache_dir.glob("*.json"):
            total += 1
            total_size += path.stat().st_size

            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    entry = CacheEntry.from_dict(data)
                    if entry.is_expired():
                        expired += 1
            except (json.JSONDecodeError, KeyError):
                expired += 1

        return {
            "total_entries": total,
            "expired_entries": expired,
            "valid_entries": total - expired,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }
