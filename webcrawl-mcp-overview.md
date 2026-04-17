# Webcrawl MCP Server

A lightweight MCP server replacement for Firecrawl, enabling Claude Code to fetch and process web content in real-time.

## Problem Statement

Claude Code needs reliable web fetching capabilities for answering questions that require current internet information. Most target pages (articles, docs, blogs) can be extracted locally with open-source libraries, so a local-first server keeps latency low and minimizes reliance on external scraping APIs.

## Solution

A self-hosted MCP server that exposes web fetching tools to Claude Code, using open-source libraries for content extraction.

## Core Tools

| Tool | Purpose | Example Use |
|------|---------|-------------|
| `web_scrape` | Fetch single URL → markdown | Reading an article, documentation page |
| `web_map` | Discover URLs on a site | Finding all docs pages before scraping |
| `web_crawl` | Fetch multiple related pages | Ingesting entire documentation site |
| `web_search` | Search the web | Finding relevant pages for a query |

## Technical Stack

### Dependencies

```toml
[project]
name = "webcrawl-mcp"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "mcp>=1.0.0",              # Anthropic MCP SDK
    "httpx>=0.27.0",           # Async HTTP client
    "trafilatura>=1.6.0",      # Content extraction (main content, strips boilerplate)
    "beautifulsoup4>=4.12.0",  # HTML parsing for URL discovery
    "markdownify>=0.11.0",     # HTML → Markdown fallback
    "duckduckgo-search>=6.0",  # Free search API (no key required)
]
```

### Why These Libraries

- **trafilatura**: Best-in-class main content extraction. Handles news sites, blogs, documentation. Removes nav, ads, footers automatically.
- **httpx**: Modern async HTTP with good timeout/retry handling
- **duckduckgo-search**: Free, no API key, reasonable rate limits
- **mcp**: Official Anthropic SDK for building MCP servers

## Architecture

```
webcrawl-mcp/
├── src/
│   └── webcrawl_mcp/
│       ├── __init__.py
│       ├── server.py       # MCP server definition, tool registration
│       ├── scraper.py      # URL fetching, content extraction
│       ├── crawler.py      # Multi-page crawling logic
│       └── search.py       # DuckDuckGo search wrapper
├── pyproject.toml
└── README.md
```

## Tool Specifications

### web_scrape

```python
@server.tool()
async def web_scrape(url: str, include_links: bool = False) -> str:
    """
    Fetch a URL and extract main content as markdown.

    Args:
        url: The URL to scrape
        include_links: Whether to preserve hyperlinks in output

    Returns:
        Markdown content of the page's main content
    """
```

### web_map

```python
@server.tool()
async def web_map(url: str, limit: int = 50) -> list[str]:
    """
    Discover URLs on a website.

    Args:
        url: Starting URL to map from
        limit: Maximum URLs to return

    Returns:
        List of discovered URLs
    """
```

### web_crawl

```python
@server.tool()
async def web_crawl(
    url: str,
    max_pages: int = 10,
    max_depth: int = 2,
    include_patterns: list[str] | None = None
) -> list[dict]:
    """
    Crawl multiple pages and extract content.

    Args:
        url: Starting URL
        max_pages: Maximum pages to fetch
        max_depth: Maximum link depth from start
        include_patterns: URL patterns to include (glob-style)

    Returns:
        List of {url, title, content} dicts
    """
```

### web_search

```python
@server.tool()
async def web_search(
    query: str,
    num_results: int = 5,
    scrape_results: bool = True
) -> list[dict]:
    """
    Search the web and optionally scrape results.

    Args:
        query: Search query
        num_results: Number of results to return
        scrape_results: Whether to fetch full content of results

    Returns:
        List of {url, title, snippet, content?} dicts
    """
```

## Claude Code Integration

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "webcrawl": {
      "command": "python",
      "args": ["-m", "webcrawl_mcp.server"],
      "env": {
        "USER_AGENT": "Mozilla/5.0 (compatible; ClaudeBot/1.0)"
      }
    }
  }
}
```

Or with uvx (if published to PyPI):

```json
{
  "mcpServers": {
    "webcrawl": {
      "command": "uvx",
      "args": ["webcrawl-mcp"]
    }
  }
}
```

## Configuration Options

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `USER_AGENT` | Generic bot UA | HTTP User-Agent header |
| `REQUEST_TIMEOUT` | `30` | Seconds before request timeout |
| `RATE_LIMIT_DELAY` | `1.0` | Seconds between requests to same domain |
| `MAX_CONTENT_LENGTH` | `500000` | Max characters to return per page |
| `CACHE_TTL` | `900` | Seconds to cache responses (0 to disable) |

## Implementation Notes

### Content Extraction Strategy

1. Try `trafilatura.extract()` with fallback settings
2. If fails or returns minimal content, fall back to `markdownify` on full HTML
3. Truncate to `MAX_CONTENT_LENGTH` if needed

### Firecrawl Fallback Strategy

When lightweight extraction returns low-quality results, fall back to Firecrawl for JS rendering:

```python
async def smart_fetch(url: str) -> str:
    """Try lightweight extraction first, fall back to Firecrawl if needed."""
    content = await trafilatura_extract(url)

    if _is_low_quality(content):
        return await firecrawl_scrape(url)  # JS rendering path

    return content

def _is_low_quality(content: str | None) -> bool:
    if not content:
        return True
    if len(content) < 200:  # Suspiciously short
        return True
    return False
```

**Fallback triggers:**
- Empty or None response from trafilatura
- Content shorter than 200 characters (likely just nav/footer fragments)
- Known JS-heavy domains (optional domain allowlist for direct Firecrawl routing)

This strategy routes ~80% of static content through the free local extraction while preserving Firecrawl for sites that genuinely require JavaScript rendering.

### Rate Limiting

- Track last request time per domain
- Enforce minimum delay between requests to same domain
- Respect `Retry-After` headers

### Caching

- Simple in-memory LRU cache with TTL
- Key: URL (normalized)
- Reduces repeated fetches during multi-turn conversations

### Error Handling

- Return structured errors, don't throw
- Include HTTP status codes when relevant
- Timeout gracefully with partial content if possible

## Comparison with Firecrawl

| Feature | Firecrawl | webcrawl-mcp |
|---------|-----------|---------------|
| Single URL scrape | Yes | Yes |
| Site mapping | Yes | Yes |
| Crawling | Yes | Yes |
| Search | Yes | Yes (DuckDuckGo) |
| JavaScript rendering | Yes | No (could add with playwright) |
| Structured extraction | Yes | No (not needed for Q&A) |
| Cost | $0-100+/mo | Free (self-hosted) |
| Rate limits | Platform-imposed | Self-controlled |

### What's Missing (Acceptable Tradeoffs)

- **JavaScript rendering**: Most content doesn't need it. Could add Playwright later if needed.
- **Structured extraction**: Not needed for general Q&A—markdown is sufficient.
- **Anti-bot bypassing**: Respect robots.txt, don't try to bypass protections.

## Future Enhancements

1. **Playwright integration** for JS-heavy sites (optional dependency)
2. **robots.txt respect** with caching
3. **Persistent cache** (SQLite) for longer-term storage
4. **PDF URL handling** - detect and process PDFs via existing pipeline
5. **Screenshot capture** for visual content

## Development Milestones

### v0.1 - MVP
- [ ] Basic MCP server setup
- [ ] `web_scrape` tool with trafilatura
- [ ] `web_search` tool with DuckDuckGo
- [ ] In-memory caching
- [ ] Claude Code integration tested

### v0.2 - Crawling
- [ ] `web_map` tool
- [ ] `web_crawl` tool
- [ ] Rate limiting per domain
- [ ] URL normalization

### v0.3 - Polish
- [ ] Configurable via environment
- [ ] Better error messages
- [ ] Logging/debugging support
- [ ] Documentation
