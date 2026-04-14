#!/usr/bin/env python3
"""
Taiwan Company Data MCP Server — Playwright-powered structured data extraction.

Exposes three tools to Claude Code:
  - tw_company_lookup: Official MOEA registry + twincn cross-reference
  - tw_person_network: Find all companies associated with a person
  - headless_fetch: Generic JS-rendered page fetch (catch-all)

Usage:
  python scripts/mcp/tw-data-server.py

Configure in .claude/settings.json:
  "mcpServers": {
    "tw-data": {
      "command": "scripts/mcp/.venv/bin/python3",
      "args": ["scripts/mcp/tw-data-server.py"]
    }
  }
"""

import asyncio
import json
import time
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

# Lazy browser import — only start Playwright when first tool call arrives
_browser = None
_playwright = None
_last_request_time: dict[str, float] = {}
RATE_LIMIT_SECONDS = 5  # Per-domain cooldown


async def _get_browser():
    """Lazy-init browser on first use, reuse across calls."""
    global _browser, _playwright
    if _browser is None:
        from playwright.async_api import async_playwright

        _playwright = await async_playwright().__aenter__()
        _browser = await _playwright.chromium.launch(headless=True)
    return _browser


async def _get_page():
    """Create a new page from the shared browser."""
    browser = await _get_browser()
    return await browser.new_page()


async def _rate_limit(domain: str):
    """Enforce per-domain rate limiting."""
    now = time.time()
    last = _last_request_time.get(domain, 0)
    wait = RATE_LIMIT_SECONDS - (now - last)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_request_time[domain] = time.time()


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


async def _tw_company_lookup(tax_id: str) -> dict:
    """
    Look up a Taiwan company by tax ID (統一編號).
    Hits findbiz.nat.gov.tw (official) + twincn.com (supplementary).
    """
    from extractors.findbiz import extract_company
    from extractors.twincn import extract_company_directors

    page = await _get_page()
    try:
        # Primary: official MOEA registry
        await _rate_limit("findbiz.nat.gov.tw")
        result = await extract_company(page, tax_id)

        if "error" not in result:
            # Supplementary: twincn for additional cross-reference
            try:
                await _rate_limit("twincn.com")
                twincn_data = await extract_company_directors(page, tax_id)
                if "error" not in twincn_data:
                    result["twincn_cross_ref"] = twincn_data
            except Exception:
                result["twincn_cross_ref"] = {"error": "twincn fetch failed"}

        return result
    finally:
        await page.close()


async def _tw_person_network(person_name: str) -> list[dict]:
    """
    Find all companies associated with a person name.
    Hits twincn.com person search.
    """
    from extractors.twincn import extract_person_network

    page = await _get_page()
    try:
        await _rate_limit("twincn.com")
        return await extract_person_network(page, person_name)
    finally:
        await page.close()


async def _headless_fetch(url: str, wait_selector: str | None = None) -> str:
    """
    Generic Playwright fetch for any JS-rendered page.
    Returns page text content as markdown-ish format.
    """
    from urllib.parse import urlparse

    domain = urlparse(url).netloc
    page = await _get_page()
    try:
        await _rate_limit(domain)
        await page.goto(url, wait_until="networkidle")

        if wait_selector:
            try:
                await page.wait_for_selector(wait_selector, timeout=10000)
            except Exception:
                pass  # Proceed with what we have

        await asyncio.sleep(2)
        text = await page.inner_text("body")
        return text[:50000]  # Cap at 50k chars
    finally:
        await page.close()


# ---------------------------------------------------------------------------
# MCP Server setup
# ---------------------------------------------------------------------------

server = Server("tw-data")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="tw_company_lookup",
            description=(
                "查詢台灣公司登記資料。輸入統一編號（8 位數字），回傳官方 MOEA 登記資料，"
                "包含公司名稱、代表人、董監事、資本額、地址、設立日期、營業項目等結構化 JSON。"
                "資料來源：findbiz.nat.gov.tw（官方）+ twincn.com（補充）。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tax_id": {
                        "type": "string",
                        "description": "台灣統一編號（8 位數字）",
                    }
                },
                "required": ["tax_id"],
            },
        ),
        Tool(
            name="tw_person_network",
            description=(
                "搜尋某人名下的所有台灣法人。輸入人名，回傳該人擔任董事/監察人/負責人的所有公司清單。"
                "資料來源：twincn.com。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "person_name": {
                        "type": "string",
                        "description": "要搜尋的人名（中文）",
                    }
                },
                "required": ["person_name"],
            },
        ),
        Tool(
            name="headless_fetch",
            description=(
                "通用 Playwright headless browser fetch。用於抓取 JS 渲染的網頁（web_fetch 黑名單上的站點）。"
                "回傳頁面文字內容。適用於 104.com.tw、twincn.com 等 JS-rendered 站點。"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "要抓取的 URL",
                    },
                    "wait_selector": {
                        "type": "string",
                        "description": "等待特定 CSS selector 出現後再擷取（選填）",
                    },
                },
                "required": ["url"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        if name == "tw_company_lookup":
            result = await _tw_company_lookup(arguments["tax_id"])
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "tw_person_network":
            result = await _tw_person_network(arguments["person_name"])
            return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

        elif name == "headless_fetch":
            text = await _headless_fetch(
                arguments["url"],
                arguments.get("wait_selector"),
            )
            return [TextContent(type="text", text=text)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, ensure_ascii=False))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
