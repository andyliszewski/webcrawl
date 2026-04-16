# PRD: Webcrawl MCP Server

> Lightweight PRD for webcrawl-mcp. Technical details in [webcrawl-mcp-overview.md](./webcrawl-mcp-overview.md).

## Problem

Firecrawl's free tier is too restrictive for regular use, and the paid tier ($100/mo) is expensive for a tool that's "nice to have" rather than mission-critical. Claude Code needs reliable web fetching for research tasks, but not at that price point.

## User

**Primary:** Developer using Claude Code who occasionally needs to fetch web content (documentation, articles, current information) during coding sessions.

**Context:** Solo developer, local machine, comfortable with Python tooling.

## User Stories

| Priority | Story |
|----------|-------|
| P0 | As a dev, I want to fetch a single URL and get readable markdown so I can understand documentation or articles |
| P0 | As a dev, I want to search the web and get summarized results so Claude can answer questions requiring current info |
| P1 | As a dev, I want to discover all URLs on a site so I can decide what to crawl |
| P1 | As a dev, I want to crawl multiple related pages so I can ingest entire doc sites |
| P2 | As a dev, I want failed lightweight fetches to fall back to Firecrawl so JS-heavy sites still work |

## Success Criteria

1. **Works:** MCP server starts, Claude Code sees the tools, basic fetch returns content
2. **Useful:** Successfully extracts readable content from common site types (docs, blogs, news)
3. **Replaces Firecrawl for 80%+ of use cases:** Most fetches don't need JS rendering

## Scope

### In Scope (MVP)
- `web_scrape`: Single URL → markdown
- `web_search`: DuckDuckGo search with optional content fetch
- In-memory caching
- Basic rate limiting
- Claude Code integration

### In Scope (v0.2)
- `web_map`: URL discovery
- `web_crawl`: Multi-page fetching

### Out of Scope
- JavaScript rendering (Firecrawl fallback handles this)
- Anti-bot bypass (respect robots.txt)
- Structured data extraction (markdown is sufficient)
- Multi-user / hosted deployment
- Persistent storage

## Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Startup time | < 2 seconds |
| Single page fetch | < 5 seconds typical |
| Memory usage | < 100MB baseline |
| Dependencies | Minimal, no heavy frameworks |

## Risks

| Risk | Mitigation |
|------|------------|
| DuckDuckGo rate limits | Respect delays, cache aggressively |
| trafilatura fails on some sites | Fall back to markdownify, then Firecrawl |
| Sites block bot UA | Configurable User-Agent |

## Acceptance Criteria (MVP)

- [ ] `web_scrape` returns markdown from https://docs.python.org/3/library/asyncio.html
- [ ] `web_scrape` returns markdown from a Medium article
- [ ] `web_search` returns results for "python asyncio tutorial"
- [ ] Claude Code can invoke all tools via MCP
- [ ] Repeated fetches hit cache (verified via logs)
- [ ] Server handles timeout gracefully (returns error, doesn't crash)

## References

- Technical Design: [webcrawl-mcp-overview.md](./webcrawl-mcp-overview.md)
