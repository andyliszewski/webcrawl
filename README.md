# webcrawl-mcp

[![PyPI version](https://img.shields.io/pypi/v/webcrawl-mcp.svg)](https://pypi.org/project/webcrawl-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/webcrawl-mcp.svg)](https://pypi.org/project/webcrawl-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A lightweight MCP server that gives Claude Code (or any MCP client) the ability to scrape, search, map, and crawl the web — using free, open-source libraries. Firecrawl is supported as an **optional** fallback for JS-heavy sites when you have a key.

## Why

Most scraping doesn't actually need a headless browser. `trafilatura` handles the ~80% case (articles, docs, blogs) locally, which is faster and keeps external API usage to a minimum. This server routes the easy stuff through local extraction and only falls back to Firecrawl when content quality is genuinely poor.

## Tools

| Tool | Purpose |
|------|---------|
| `webcrawl_scrape` | Fetch a single URL → markdown |
| `webcrawl_search` | DuckDuckGo search (optionally scrape results) |
| `webcrawl_map` | Discover same-domain URLs from a starting page |
| `webcrawl_crawl` | BFS crawl multiple pages |

## Install

```bash
pip install webcrawl-mcp
```

Requires Python 3.12+.

Quick smoke test (should print `Webcrawl MCP server running` then exit cleanly with Ctrl-C):

```bash
webcrawl-mcp
```

### Install from source (for development)

```bash
git clone https://github.com/andyliszewski/webcrawl-mcp.git
cd webcrawl-mcp
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -e .
```

## Configure your MCP client

### Claude Code

Create `.mcp.json` in your project root (or merge into `~/.claude/settings.json`):

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

This uses [`uvx`](https://docs.astral.sh/uv/guides/tools/) to run the package in a temporary environment — no manual install needed. If `uvx` is unavailable, install via `pip install webcrawl-mcp` and use `"command": "webcrawl-mcp"` with no args instead.

For a source checkout (development), point `command` at your venv's Python and use `"args": ["-m", "webcrawl_mcp"]`.

Then in a Claude Code session run `/mcp` — you should see `webcrawl` listed with four tools.

### Claude Desktop

Same JSON shape, placed in `claude_desktop_config.json` (see [Anthropic's docs](https://modelcontextprotocol.io/quickstart/user) for the OS-specific path). Restart Claude Desktop after editing.

### Other MCP clients (Cursor, Cline, Continue, Zed, etc.)

The `command` / `args` / `env` shape is standardized. Consult your client's MCP docs for where to put it.

## Verify it's working

Ask your agent something like:

> Use the `webcrawl_scrape` tool to fetch `https://docs.python.org/3/library/asyncio.html` and summarize the first section.

You should see the tool invocation in the client UI, followed by a summary grounded in the live page content. If nothing happens, see [Troubleshooting](#troubleshooting).

## Environment variables

All optional:

| Variable | Default | Purpose |
|----------|---------|---------|
| `USER_AGENT` | `Mozilla/5.0 (compatible; WebcrawlMCP/1.0; …)` | HTTP User-Agent |
| `REQUEST_TIMEOUT` | `30` | Seconds before request timeout |
| `FIRECRAWL_API_KEY` | *(unset)* | If set, enables Firecrawl fallback for low-quality extractions. **Leave unset for a fully free setup.** |
| `FIRECRAWL_API_URL` | `https://api.firecrawl.dev/v1` | Firecrawl endpoint |

Set these inside the `env` block of your MCP config, not in your shell — MCP servers run under the client, not your terminal.

## Fallback behavior

1. `trafilatura` extracts main content from HTML.
2. If that fails or returns <200 chars, `markdownify` converts the raw HTML.
3. If the result is still low-quality **and** `FIRECRAWL_API_KEY` is set, Firecrawl is used as a last resort.

Without a Firecrawl key, the tool is fully self-contained and free.

## Troubleshooting

**Client doesn't list `webcrawl` under MCP servers.**
The `command` path is almost always the problem. It must be an absolute path to the Python binary *inside* your venv, not just `python`. Test it in a terminal: `/path/you/configured -m webcrawl_mcp` should print `Webcrawl MCP server running`.

**`ModuleNotFoundError: webcrawl_mcp`.**
Either `pip install -e .` didn't run in the same venv as `command`, or `PYTHONPATH` is missing/wrong. Double-check both point at the same checkout.

**Python version mismatch.**
Requires 3.12+. `python --version` inside your venv should report ≥ 3.12. If not, recreate the venv with a newer Python.

**Scrapes return very little text.**
Some sites render with JavaScript and can't be extracted statically. Either set `FIRECRAWL_API_KEY` to enable the fallback path, or accept that this tool isn't the right fit for that specific site.

**Search is slow or rate-limited.**
DuckDuckGo throttles bursty querying. Space out searches, or reduce `num_results`.

## Responsible use

This tool is for fetching public web content for research, coding assistance, and similar legitimate uses. You are responsible for:

- Respecting each target site's Terms of Service and `robots.txt`.
- Not overloading servers — the built-in per-domain rate limiter helps, but don't circumvent it.
- Complying with applicable laws around automated access and data use in your jurisdiction.

## License

MIT — see [LICENSE](LICENSE).

## Acknowledgements

Built on top of [`trafilatura`](https://github.com/adbar/trafilatura), [`httpx`](https://www.python-httpx.org/), [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/), [`markdownify`](https://github.com/matthewwithanm/python-markdownify), [`ddgs`](https://github.com/deedy5/ddgs), and [`fastmcp`](https://github.com/jlowin/fastmcp). Firecrawl integration uses the public [Firecrawl API](https://firecrawl.dev) (not affiliated).
