"""LRU cache with TTL support for scraped content."""

import os
import sys
import time
from collections import OrderedDict
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

DEFAULT_CACHE_TTL = int(os.environ.get("CACHE_TTL", "900"))  # 15 minutes
DEFAULT_CACHE_SIZE = int(os.environ.get("CACHE_SIZE", "100"))


def normalize_url(url: str) -> str:
    """Normalize URL for use as cache key.

    - Lowercases scheme and host
    - Sorts query parameters
    - Removes default ports
    - Removes trailing slashes from path

    Args:
        url: URL to normalize

    Returns:
        Normalized URL string
    """
    parsed = urlparse(url)

    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()

    # Remove default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]

    # Normalize path (remove trailing slash, but keep root)
    path = parsed.path.rstrip("/") or "/"

    # Sort query parameters
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    sorted_query = urlencode(sorted(query_params))

    return urlunparse((scheme, netloc, path, "", sorted_query, ""))


class TTLCache:
    """LRU cache with TTL expiration."""

    def __init__(self, maxsize: int = DEFAULT_CACHE_SIZE, ttl: int = DEFAULT_CACHE_TTL):
        """Initialize cache.

        Args:
            maxsize: Maximum number of entries
            ttl: Time-to-live in seconds (0 disables caching)
        """
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache: OrderedDict[str, tuple[float, str]] = OrderedDict()

    @property
    def enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.ttl > 0

    def get(self, url: str) -> str | None:
        """Get cached content for URL.

        Args:
            url: URL to look up

        Returns:
            Cached content if found and not expired, None otherwise
        """
        if not self.enabled:
            return None

        key = normalize_url(url)

        if key not in self._cache:
            return None

        timestamp, content = self._cache[key]

        # Check if expired
        if time.time() - timestamp > self.ttl:
            del self._cache[key]
            print(f"[webcrawl] cache expired: {url}", file=sys.stderr)
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        print(f"[webcrawl] cache hit: {url}", file=sys.stderr)
        return content

    def set(self, url: str, content: str) -> None:
        """Store content in cache.

        Args:
            url: URL as key
            content: Content to cache
        """
        if not self.enabled:
            return

        key = normalize_url(url)

        # Remove oldest entries if at capacity
        while len(self._cache) >= self.maxsize:
            self._cache.popitem(last=False)

        self._cache[key] = (time.time(), content)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)


# Global cache instance
cache = TTLCache()
