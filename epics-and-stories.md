# Epics and Stories: Webcrawl MCP

## Epic 1: Project Foundation

### Story 1.1: Project Setup
**As a** developer
**I want** the project scaffolded with dependencies
**So that** I can start implementing features

**Acceptance Criteria:**
- [x] Python project with `pyproject.toml` (Python 3.12+)
- [x] Dependencies: mcp, httpx, trafilatura, beautifulsoup4, markdownify, duckduckgo-search
- [x] Directory structure: `src/webcrawl_mcp/` with `__init__.py`, `server.py`
- [x] Can run `python -m webcrawl_mcp.server` without errors

### Story 1.2: MCP Server Skeleton
**As a** developer
**I want** a minimal MCP server that starts and registers with Claude Code
**So that** I have the foundation for adding tools

**Acceptance Criteria:**
- [x] Server starts and logs "Webcrawl MCP server running"
- [x] Server registers with Claude Code via settings.json config
- [ ] Claude Code shows the server as connected (manual verification required)

---

## Epic 2: Single URL Scraping (P0)

### Story 2.1: Basic URL Fetch
**As a** dev using Claude Code
**I want** to fetch a URL and get markdown content
**So that** I can read documentation or articles

**Acceptance Criteria:**
- [x] `web_scrape(url: str)` tool registered
- [x] Fetches URL with httpx, configurable timeout
- [x] Extracts main content with trafilatura
- [x] Returns markdown string
- [x] Works on: docs.python.org, a blog post, a news article

### Story 2.2: Extraction Fallback
**As a** dev
**I want** failed trafilatura extractions to fall back to markdownify
**So that** I still get usable content from difficult pages

**Acceptance Criteria:**
- [x] If trafilatura returns None or < 200 chars, use markdownify on raw HTML
- [x] Fallback content is still reasonably readable
- [x] Logs which extraction method was used

### Story 2.3: Content Caching
**As a** dev
**I want** repeated fetches of the same URL to hit cache
**So that** I don't waste time re-fetching during multi-turn conversations

**Acceptance Criteria:**
- [x] LRU cache with configurable TTL (default 15 min)
- [x] Cache key is normalized URL
- [x] Cache hit logged for debugging
- [x] `CACHE_TTL` env var controls TTL (0 disables)

### Story 2.4: Rate Limiting
**As a** dev
**I want** requests to the same domain rate-limited
**So that** I don't get blocked or overload servers

**Acceptance Criteria:**
- [x] Track last request time per domain
- [x] Enforce minimum delay between requests (default 1s)
- [x] `RATE_LIMIT_DELAY` env var configurable
- [x] Respects `Retry-After` header if present

---

## Epic 3: Web Search (P0)

### Story 3.1: DuckDuckGo Search
**As a** dev
**I want** to search the web and get results
**So that** Claude can answer questions requiring current information

**Acceptance Criteria:**
- [x] `web_search(query: str, num_results: int = 5)` tool registered
- [x] Returns list of `{url, title, snippet}`
- [x] Works for general queries like "python asyncio tutorial 2024"

### Story 3.2: Search with Content Fetch
**As a** dev
**I want** search results to optionally include full page content
**So that** Claude gets more context without separate fetches

**Acceptance Criteria:**
- [x] `scrape_results: bool = False` parameter
- [x] When true, fetches each result URL and adds `content` field
- [x] Respects rate limiting between fetches
- [x] Gracefully handles fetch failures (returns result without content)

---

## Epic 4: URL Discovery & Crawling (P1 - v0.2)

### Story 4.1: Site URL Mapping
**As a** dev
**I want** to discover all URLs on a site
**So that** I can decide what pages to crawl

**Acceptance Criteria:**
- [x] `web_map(url: str, limit: int = 50)` tool registered
- [x] Extracts links from page HTML using BeautifulSoup
- [x] Filters to same-domain links only
- [x] Returns list of unique URLs
- [x] Respects limit parameter

### Story 4.2: Multi-Page Crawling
**As a** dev
**I want** to crawl multiple related pages
**So that** I can ingest entire documentation sites

**Acceptance Criteria:**
- [x] `web_crawl(url: str, max_pages: int = 10, max_depth: int = 2)` tool
- [x] BFS crawl from starting URL
- [x] Returns list of `{url, title, content}`
- [x] Respects rate limiting
- [x] `include_patterns` parameter for glob-style URL filtering

---

## Epic 5: Firecrawl Fallback (P2 - Future)

### Story 5.1: Intelligent Fallback
**As a** dev
**I want** failed lightweight fetches to fall back to Firecrawl
**So that** JS-heavy sites still work

**Acceptance Criteria:**
- [x] Detect low-quality extraction (empty, < 200 chars)
- [x] If Firecrawl API key configured, attempt Firecrawl scrape
- [x] Log when fallback is triggered
- [x] Works without Firecrawl (graceful degradation)

---

## Implementation Order

| Phase | Stories | Deliverable |
|-------|---------|-------------|
| MVP | 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 3.1 | Working scrape + search |
| MVP+ | 3.2 | Search with content |
| v0.2 | 4.1, 4.2 | Mapping + crawling |
| Future | 5.1 | Firecrawl fallback |
