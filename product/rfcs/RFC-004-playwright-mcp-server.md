# RFC-004：Playwright MCP Server — 台灣公司資料結構化爬蟲

| 欄位 | 內容 |
|------|------|
| **狀態** | Draft |
| **建立日期** | 2026-04-14 |
| **最後更新** | 2026-04-14 |
| **作者** | Andrew + Claude |
| **對應版本** | v1.8 |
| **CHANGELOG entry** | [v1.8](../../CHANGELOG.md#v18) |
| **PRD 章節** | [PRD § 迭代路線圖](../PRD.md#迭代路線圖) |
| **相關 commit** | TBD |

---

## 1. Summary

新增一個 Playwright-powered MCP server（`scripts/mcp/tw-data-server.py`），暴露三個工具給 Agent：`tw_company_lookup`（台灣公司登記資料）、`tw_person_network`（關聯法人搜尋）、`headless_fetch`（通用 JS 渲染頁面抓取）。這三個工具取代目前 entity verification 階段在 JS 黑名單站點間繞路的低效搜尋模式，將 5-8 次 search + 2-4 次 fetch 壓縮為 1-2 次 MCP call + 1 次驗證 search。`headless_fetch` 同時作為未來遇到新 JS 站點的通用 catch-all。

**為什麼現在做**：6 個案例的 case-log 顯示每案約 25-45% 的搜尋預算浪費在 JS 渲染站（twincn、104、findbiz）的繞路上。最近的雲端整合代理商 D案例（2026-04-14）再次印證：光確認「誰是現任代表人」就用了 4 個來源 8 次搜尋，原因只是官方源 findbiz.nat.gov.tw 是 JS 渲染。

## 2. Background / Problem

### 觀察到的問題

| 案例 | 問題 | 浪費 |
|------|------|------|
| 雲端整合代理商 D（2026-04-14） | opengovtw 顯示舊代表人（代表人 X vs 代表人 Y），需 3 源交叉比對 | fetch 超出預估 +40% |
| 微型系統整合商 E（2026-04-12） | 雙法人同址同負責人，需額外 fetch 超出預算 | +2 fetch |
| 微型公司 F（2026-04-08） | 104.com.tw 員工數拿不到（Vite SPA），3 次 fallback 搜尋全失敗 | 3 search 浪費 |
| v1.2 起源事件 | opengovtw 董監事名單與商工署不同步，導致報告寫入過時資料 | 催生整套交叉比對流程 |

### 現況的限制

`entity-verification.md` 定義了 5 步交叉比對流程，使用三個**民間鏡像站**（biz.news.org.tw、twincn.com snippet、opengovtw.com），因為**官方源 findbiz.nat.gov.tw 是 JS 渲染，web_fetch 無法取得內容**。

`fetch-policy.md` 維護 6 站黑名單，全因 JS 渲染或登入牆：

| 站點 | 類型 | 問題 | 影響 |
|------|------|------|------|
| twincn.com | 公司登記 | JS 渲染 | **高**：董監事歷史的唯一來源 |
| 104.com.tw | 求職平台 | Vite SPA | **高**：員工數主要來源 |
| findcompany.com.tw | 公司查詢 | 403 Forbidden | 中 |
| twfile.com | 公司情報 | JS 渲染 | 中（與 twincn 重複） |
| linkedin.com | 職業社群 | 登入牆 | 高（但 MCP 也無法突破登入牆） |
| alphaloan.co | 公司資訊 | 410 Gone | 低（已關站） |

其中 twincn.com 和 104.com.tw 的問題**純粹是 JS 渲染**，Playwright 一行搞定。

## 3. Goals / Non-goals

### Goals

- **G1**：透過 Playwright 直接存取 findbiz.nat.gov.tw（商工署官方），取代民間鏡像站交叉比對
- **G2**：透過 Playwright 渲染 twincn.com 完整頁面，取得完整董監事 + 變更歷史
- **G3**：透過 Playwright 渲染 104.com.tw 公司頁面，取得員工數
- **G4**：Entity verification 搜尋預算降低 40-60%
- **G5**：提供 `headless_fetch` 通用工具，作為未來遇到新 JS 站的 catch-all
- **G6**：零外部 API key，全用公開台灣政府/商業資料源

### Non-goals

- 不做通用爬蟲/蜘蛛
- 不突破登入牆（LinkedIn、付費資料庫仍為 OSINT 天花板）
- 不取代 web_search（MCP 工具是補充，不是替代）
- 不支援非台灣登記系統（日本 EDINET、韓國 DART 延後至未來 RFC）
- 不做 CAPTCHA 自動解碼
- 不讓 Agent 在 session 中動態新增 extractor（MCP server 是獨立 process，mid-session 修改需重啟）

## 4. Options Considered

### Option A: Python + Playwright MCP Server

在 `scripts/mcp/` 建立 Python MCP server，使用 `playwright` Python bindings + `mcp` Python SDK（stdio transport）。暴露 3 個工具，每個工具內含專用 HTML parser。

**優點**：
- 專案已有 Python 腳本（`sync-registry.py`），不引入第二語言生態
- Python MCP SDK 穩定（stdio transport）
- Playwright Python API 成熟
- 專用 parser 產出結構化 JSON，Agent 不需解析 HTML

**缺點**：
- 需 `pip install playwright mcp` + `playwright install chromium`（~400MB）
- Python MCP SDK 文件量少於 TypeScript

### Option B: Node.js + Playwright MCP Server

同樣的工具設計，但用 Node.js + TypeScript MCP SDK。

**優點**：
- MCP TypeScript SDK 是官方 reference implementation
- Playwright 原生是 JS 專案

**缺點**：
- 引入 Node.js 第二 runtime（專案目前純 Python）
- `package.json` + `node_modules` 管理成本
- 團隊較不熟

### Option C: 使用社群 Playwright MCP Server

直接用 `@anthropic/mcp-playwright` 或類似社群套件。

**優點**：
- 零開發成本

**缺點**：
- 無台灣特定結構化解析（Agent 仍需自己解析 HTML）
- 無速率限制、無降級策略
- 無法控制輸出格式

## 5. Decision

**選擇**：Option A（Python + Playwright）

**理由**：專案已有 Python 腳本基礎；MCP server 的核心價值在於**台灣特定的 HTML 解析邏輯**（findbiz 表格結構、twincn 董監事表格、104 公司頁面），這是 domain logic，用團隊熟悉的語言寫最合理。引入 Node.js 只因為「MCP SDK 官方是 TS」不值得——Python SDK 對 stdio transport 完全夠用。

Option C 看似零成本但核心問題沒解：Agent 還是要自己解析 HTML，等於把 Playwright 當成 `web_fetch` 的加速版，沒拿到結構化資料的真正好處。

### 關鍵決策點

| 決策 | 選擇 | 原因 |
|------|------|------|
| 語言 | Python | 專案一致性；不引入第二 runtime |
| 位置 | `scripts/mcp/` | 平行於 `scripts/sync-registry.py` |
| Transport | stdio | Claude Code 原生 MCP 使用 stdio |
| 瀏覽器生命週期 | 首次呼叫啟動、跨呼叫複用、server 關閉時釋放 | 避免每次 2-3 秒冷啟動 |
| 速率限制 | 同域名 5 秒間隔 | 尊重公共資料源 |
| 降級策略 | MCP 不可用 → 回退現有 web_search 流程 | 零回歸風險 |
| 交叉驗證 | MCP 資料算 1 個來源，仍需 1 個 web 來源交叉 | 維持 v1.2 安全保證 |
| 預算計入 | MCP call 計入 fetch 預算 | 不膨脹既有預算框架 |
| 擴展策略 | L1 headless_fetch catch-all → L2 case-log 沉澱 → L3 批次補 extractor | 見下方「未知站點」章節 |

### 未知站點的擴展策略

三個專用 extractor 只覆蓋已知痛點。處理策略分三層：

| 層級 | 情境 | 做法 | 負責 |
|------|------|------|------|
| **L1** | 分析中首次遇到新 JS 站 | `headless_fetch(url)` 通用工具，回傳 markdown | Agent 自動 |
| **L2** | 同站出現 2+ 案例 | case-log 記錄 → 下次迭代評估 | PM 判斷 |
| **L3** | 確認值得 | 新增 `scripts/mcp/extractors/{site}.py` | 開發 |

`headless_fetch` 作為 L1 catch-all，確保系統在遇到任何新 JS 站時不會退化到「搜不到就放棄」。

## 6. 效能影響

### 設計時預估

| 維度 | 變更前 | 變更後 | Δ |
|------|--------|--------|---|
| 預載 token（系統 prompt + skill + agent） | ~2,700 | ~2,900 | +200（AGENT-CORE 加 MCP 說明） |
| Entity verification: avg search | 5-8 | 2-3 | **-3 to -5** |
| Entity verification: avg fetch | 2-4 | 0-1 | **-2 to -3** |
| Entity verification: avg MCP call | 0 | 1-2 | +1-2 |
| 員工數驗證: avg search | 2-3（常失敗） | 0-1 | **-2** |
| 員工數驗證: avg MCP call | 0 | 1 | +1 |
| 命中率預期變化 | 0.5-0.7 | 0.6-0.8 | +0.05~0.1（減少無效搜尋） |
| 證據等級分布 | 較多 [部分證據] | 更多充分證據 | 官方源取代民間鏡像 |
| 每案 wall clock time | — | — | **-3 to -5 分鐘** |

### 實測結果

> 實作完成後回填。

| 維度 | 預估 | 實測 | 偏差 | 備註 |
|------|------|------|------|------|
| | | | | |

**測試案例**：TBD
**測試日期**：TBD
**對照 baseline**：[baseline-v1.1-token-usage.md](../perf/baseline-v1.1-token-usage.md)

## 7. 風險

| 風險 | 嚴重度 | 緩解方式 |
|------|--------|---------|
| findbiz.nat.gov.tw 改版，parser 壞掉 | 高 | CSS selector 版本固定；server 啟動時 health check；壞了回退原流程 |
| Playwright/Chromium 二進位大（~400MB） | 中 | 一次性安裝；README 文件化；.gitignore 排除快取 |
| MCP server process 分析中 crash | 中 | Agent 偵測 tool failure → 回退 web_search 流程 |
| 台灣政府站點 rate limit / IP block | 中 | 同域名 5 秒間隔；exponential backoff；5 分鐘結果快取 |
| 使用者環境無法安裝 Playwright（企業 proxy 等） | 低 | MCP server 是 optional，所有現有流程保持運作 |
| Headless 偵測（反爬） | 低 | 政府站點通常不反爬；必要時加 stealth 設定 |

## 8. Implementation Plan

### 需要新增的檔案

- `scripts/mcp/tw-data-server.py` — MCP server 主程式（Python, stdio, 3 tools）
- `scripts/mcp/extractors/__init__.py` — Package init
- `scripts/mcp/extractors/findbiz.py` — findbiz.nat.gov.tw 頁面解析
- `scripts/mcp/extractors/twincn.py` — twincn.com 董監事表格解析
- `scripts/mcp/extractors/job104.py` — 104.com.tw 公司頁面解析
- `scripts/mcp/requirements.txt` — Python 依賴
- `scripts/mcp/README.md` — 安裝與使用指南

### 需要修改的檔案

- `.claude/settings.json` — 加 `mcpServers.tw-data` 設定
- `agent/AGENT-CORE.md` — 數據源優先序加 MCP；搜尋預算表加「有 MCP」欄
- `agent/prompts/entity-verification.md` — 新增「MCP 工具優先流程」段落
- `references/methodology/fetch-policy.md` — 黑名單加「MCP 替代」註解
- `product/rfcs/README.md` — RFC 索引加 RFC-004
- `product/PRD.md` — 迭代路線圖加 v1.8
- `product/architecture.md` — 架構圖加 MCP 層
- `CHANGELOG.md` — v1.8 release notes（Phase 3）

### 不動的檔案

- `.claude/skills/recon/SKILL.md`、`company/SKILL.md`、`industry/SKILL.md` — 委派給 entity-verification prompt
- `.claude/rules/output-quality.md` — MCP 資料用同一套證據等級
- `references/methodology/quality-checklist.md` — 既有檢查項已涵蓋
- `agent/prompts/stakeholder-investigation.md` 等其他 prompt — 間接受益，不需改動
- `scripts/sync-registry.py` — 完全無關

## 9. Followups / Open Questions

- **F1**：`tw_company_lookup` 是否應在 session 內快取結果？同一統編重複查詢（如 stakeholder 階段查關聯法人後 deep-dive 又查一次）可省 1 次 call
- **F2**：是否支援批次查詢（一次傳多個統編）？微型系統整合商 E案例有雙法人需求
- **F3**：`headless_fetch` 是否應完全取代 fetch-policy 黑名單概念？（任何 JS 站都可以打了）
- **F4**：是否新增 `tw_court_search`（司法院裁判書系統）作為第四工具？多個 case-log 記錄搜尋失敗
- **F5**：L2 沉澱機制：case-log 的「有效搜尋策略」欄位是否需要結構化（新增「建議新增 MCP extractor」標記），以便系統性追蹤
- **F6**：考慮擴展至 gcis.nat.gov.tw（商業司，含獨資/合夥事業），目前只覆蓋公司登記

## 10. References

- `agent/prompts/entity-verification.md` §19-39：現行台灣交叉比對流程
- `references/methodology/fetch-policy.md`：現行黑名單
- Case logs：雲端整合代理商 D、微型系統整合商 E、微型公司 F、上市遊戲營運商 C、數據新創 G、軟體新創 H
- MCP Python SDK：https://github.com/modelcontextprotocol/python-sdk
- Playwright Python：https://playwright.dev/python/
- 商工登記公示資料查詢：https://findbiz.nat.gov.tw/
