"""URL fetching and content extraction."""

import os
import sys

import httpx
import trafilatura
from markdownify import markdownify as md

from webcrawl_mcp.cache import cache
from webcrawl_mcp.rate_limiter import rate_limiter
from webcrawl_mcp.firecrawl import is_configured as firecrawl_configured, scrape_with_firecrawl

DEFAULT_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))
MIN_CONTENT_LENGTH = 200


def _is_low_quality(content: str | None) -> bool:
    """Check if content is low quality and might need Firecrawl.

    Args:
        content: Extracted content

    Returns:
        True if content is empty or suspiciously short
    """
    if not content:
        return True
    if len(content) < MIN_CONTENT_LENGTH:
        return True
    return False
DEFAULT_USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (compatible; WebcrawlMCP/1.0; +https://github.com/andyliszewski/webcrawl-mcp)",
)


def _parse_retry_after(value: str) -> float | None:
    """Parse Retry-After header value.

    Args:
        value: Header value (seconds or HTTP date)

    Returns:
        Seconds to wait, or None if unparseable
    """
    try:
        return float(value)
    except ValueError:
        # Could be HTTP date format, but we'll skip that complexity
        return None


async def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch URL content using httpx.

    Respects per-domain rate limiting and Retry-After headers.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Raw HTML content

    Raises:
        httpx.HTTPError: On request failure
    """
    # Wait for rate limit if needed
    await rate_limiter.wait_if_needed(url)

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            timeout=timeout,
            headers={"User-Agent": DEFAULT_USER_AGENT},
            follow_redirects=True,
        )

        # Record the request time
        rate_limiter.record_request(url)

        # Handle Retry-After header
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                seconds = _parse_retry_after(retry_after)
                if seconds:
                    rate_limiter.set_retry_after(url, seconds)

        response.raise_for_status()
        return response.text


def extract_with_trafilatura(html: str, url: str) -> str | None:
    """Extract main content from HTML using trafilatura.

    Args:
        html: Raw HTML content
        url: Original URL (used for link resolution)

    Returns:
        Extracted markdown content, or None if extraction fails
    """
    return trafilatura.extract(
        html,
        url=url,
        include_links=True,
        include_formatting=True,
        include_images=False,
        output_format="markdown",
    )


def extract_with_markdownify(html: str) -> str:
    """Fallback extraction using markdownify.

    Args:
        html: Raw HTML content

    Returns:
        Markdown converted from full HTML
    """
    return md(html, heading_style="ATX", strip=["script", "style", "nav", "footer"])


async def scrape(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch URL and extract main content as markdown.

    Extraction strategy:
    1. trafilatura (best for articles/docs)
    2. markdownify fallback (if trafilatura fails)
    3. Firecrawl fallback (if configured and content still low quality)

    Results are cached with configurable TTL.

    Args:
        url: The URL to scrape
        timeout: Request timeout in seconds

    Returns:
        Markdown content of the page
    """
    # Check cache first
    cached = cache.get(url)
    if cached is not None:
        return cached

    html = await fetch_url(url, timeout)

    # Try trafilatura first
    content = extract_with_trafilatura(html, url)

    if content and len(content) >= MIN_CONTENT_LENGTH:
        print(
            f"[webcrawl] trafilatura: {len(content)} chars from {url}",
            file=sys.stderr,
        )
        cache.set(url, content)
        return content

    # Fallback to markdownify
    reason = "no content" if not content else f"only {len(content)} chars"
    print(
        f"[webcrawl] trafilatura {reason}, falling back to markdownify for {url}",
        file=sys.stderr,
    )

    content = extract_with_markdownify(html)
    print(
        f"[webcrawl] markdownify: {len(content)} chars from {url}",
        file=sys.stderr,
    )

    # If still low quality and Firecrawl is configured, try Firecrawl
    if _is_low_quality(content) and firecrawl_configured():
        print(
            f"[webcrawl] content still low quality, trying Firecrawl for {url}",
            file=sys.stderr,
        )
        firecrawl_content = await scrape_with_firecrawl(url, timeout)
        if firecrawl_content and len(firecrawl_content) > len(content or ""):
            content = firecrawl_content

    cache.set(url, content)
    return content
