"""Firecrawl API fallback for JS-heavy sites."""

import os
import sys

import httpx

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
FIRECRAWL_API_URL = os.environ.get("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v1")


def is_configured() -> bool:
    """Check if Firecrawl API is configured."""
    return bool(FIRECRAWL_API_KEY)


async def scrape_with_firecrawl(url: str, timeout: int = 60) -> str | None:
    """Scrape URL using Firecrawl API.

    Args:
        url: URL to scrape
        timeout: Request timeout in seconds

    Returns:
        Markdown content or None if failed
    """
    if not is_configured():
        return None

    print(f"[webcrawl] firecrawl fallback for {url}", file=sys.stderr)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{FIRECRAWL_API_URL}/scrape",
                headers={
                    "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "url": url,
                    "formats": ["markdown"],
                },
                timeout=timeout,
            )
            response.raise_for_status()

            data = response.json()
            content = data.get("data", {}).get("markdown", "")

            if content:
                print(
                    f"[webcrawl] firecrawl: {len(content)} chars from {url}",
                    file=sys.stderr,
                )
                return content

            print(f"[webcrawl] firecrawl returned no content for {url}", file=sys.stderr)
            return None

    except httpx.HTTPStatusError as e:
        print(f"[webcrawl] firecrawl HTTP error: {e.response.status_code}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[webcrawl] firecrawl error: {e}", file=sys.stderr)
        return None
