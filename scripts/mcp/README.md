# Taiwan Company Data MCP Server

Playwright-powered MCP server，提供三個結構化台灣公司資料查詢工具給 Claude Code。

## 安裝

```bash
cd scripts/mcp
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

## 工具

| 工具名稱 | 用途 | 資料源 |
|---------|------|--------|
| `tw_company_lookup` | 台灣公司登記查詢（統一編號） | findbiz.nat.gov.tw + twincn.com |
| `tw_person_network` | 關聯法人搜尋（人名） | twincn.com |
| `headless_fetch` | 通用 JS 渲染頁面抓取 | 任何 URL |

## Claude Code 設定

在 `.claude/settings.json` 加入：

```json
{
  "mcpServers": {
    "tw-data": {
      "command": "scripts/mcp/.venv/bin/python3",
      "args": ["scripts/mcp/tw-data-server.py"]
    }
  }
}
```

## 手動測試

```bash
source .venv/bin/activate
python3 tw-data-server.py
```

Server 啟動後透過 stdio 接收 JSON-RPC。可用 MCP Inspector 測試。

## 設計

- **Lazy browser init**：首次 tool call 時才啟動 Chromium，跨 call 複用
- **Rate limiting**：同域名 5 秒間隔
- **Graceful degradation**：MCP server 不可用時，agent 回退到 web_search 流程（見 `entity-verification.md`）
- **結構化輸出**：`tw_company_lookup` 和 `tw_person_network` 回傳 JSON，agent 不需解析 HTML

## 擴展

新增 extractor：在 `extractors/` 加 `{site}.py`，在 `tw-data-server.py` 註冊新 tool。參見 [RFC-004](../../product/rfcs/RFC-004-playwright-mcp-server.md) §9 擴展策略。
