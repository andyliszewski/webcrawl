"""Web search using DuckDuckGo."""

import sys
import warnings

from ddgs import DDGS

from webcrawl_mcp.scraper import scrape

# Suppress impersonate warnings from ddgs
warnings.filterwarnings("ignore", message="Impersonate.*does not exist")


def _search_ddg(query: str, num_results: int) -> list[dict]:
    """Perform DuckDuckGo search.

    Args:
        query: Search query string
        num_results: Maximum number of results

    Returns:
        List of raw search results
    """
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=num_results):
            results.append({
                "url": r.get("href", ""),
                "title": r.get("title", ""),
                "snippet": r.get("body", ""),
            })
    return results


def search(query: str, num_results: int = 5) -> list[dict]:
    """Search the web using DuckDuckGo.

    Args:
        query: Search query string
        num_results: Maximum number of results to return

    Returns:
        List of search results with url, title, snippet
    """
    print(f"[webcrawl] searching: {query}", file=sys.stderr)
    results = _search_ddg(query, num_results)
    print(f"[webcrawl] found {len(results)} results", file=sys.stderr)
    return results


async def search_and_scrape(query: str, num_results: int = 5) -> list[dict]:
    """Search the web and fetch content for each result.

    Args:
        query: Search query string
        num_results: Maximum number of results to return

    Returns:
        List of search results with url, title, snippet, and content
    """
    print(f"[webcrawl] searching: {query}", file=sys.stderr)
    results = _search_ddg(query, num_results)
    print(f"[webcrawl] found {len(results)} results, fetching content...", file=sys.stderr)

    for result in results:
        url = result["url"]
        try:
            content = await scrape(url)
            result["content"] = content
            print(f"[webcrawl] fetched {len(content)} chars from {url}", file=sys.stderr)
        except Exception as e:
            print(f"[webcrawl] failed to fetch {url}: {e}", file=sys.stderr)
            result["content"] = None

    return results
