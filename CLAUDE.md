# Project Instructions

## Web Scraping Tool Preferences

When fetching web content, prefer the **webcrawl** MCP tools over Firecrawl:

| Task | Use | Fallback |
|------|-----|----------|
| Single page | `webcrawl_scrape` | `mcp__firecrawl__firecrawl_scrape` |
| Search | `webcrawl_search` | `mcp__firecrawl__firecrawl_search` |
| Discover URLs | `webcrawl_map` | `mcp__firecrawl__firecrawl_map` |
| Multi-page crawl | `webcrawl_crawl` | `mcp__firecrawl__firecrawl_crawl` |

**When to fall back to Firecrawl:**
- `webcrawl_scrape` returns empty or very short content (JS-heavy site)
- Site requires JavaScript rendering
- webcrawl tool fails or times out

**Why webcrawl first:**
- Free (no API costs)
- Faster for static content
- No rate limits
