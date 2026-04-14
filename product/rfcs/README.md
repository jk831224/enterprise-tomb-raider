# RFCs — 設計變更紀錄

> 每次有意義的設計變更一份 RFC。寫 RFC 不是繁文縟節，是強迫自己**至少考慮過一個替代方案**。
> 模板見 [`_RFC-template.md`](_RFC-template.md)。

## 索引

| 編號 | 標題 | 狀態 | 對應版本 | 主題 |
|------|------|------|---------|------|
| [RFC-001](RFC-001-drop-zone.md) | Drop Zone — 使用者餵資區 | Implemented | v1.4 | 把 AI 從「不可靠抓取者」轉成「可靠整合者」 |
| [RFC-002](RFC-002-hit-rate-two-dimensional.md) | 命中率雙維度改進（Hit Rate + Exploration Ratio）| Draft | v1.5（候選）| 解決單維度命中率對「高聚焦調查」的假陽性警訊 |
| [RFC-003](../rfc/RFC-003-cases-and-supplement.md) | cases/ 統一目錄 + /supplement 增量更新 | Implemented | v1.5 | 統一三散目錄結構 + 增量更新機制 |
| [RFC-004](RFC-004-playwright-mcp-server.md) | Playwright MCP Server — 台灣公司資料結構化爬蟲 | Implemented | v1.8 | 用 Playwright 解決 JS 渲染站黑名單，entity verification 搜尋量 -40~60% |
| [RFC-005](RFC-005-single-context-architecture.md) | 維持單 context 架構、不導入 subagent | Accepted | v1.8 | 記錄架構判斷門檻，避免未來重覆爭論 |

## 編號慣例

- 3 位數遞增（001, 002, 003...），不重用
- 檔名格式：`RFC-XXX-{kebab-case-title}.md`
- 即使 RFC 被 superseded 也保留原檔，只更新狀態並在新 RFC 標註 `Supersedes RFC-XXX`

## 狀態說明

| 狀態 | 意義 |
|------|------|
| **Draft** | 還在討論，未實作 |
| **Accepted** | 已決定要做，尚未實作完 |
| **Implemented** | 已實作完並合進 main |
| **Superseded by RFC-XXX** | 被新 RFC 取代，內容過時 |

## 寫 RFC 的時機

**寫**：
- 新功能影響 ≥2 個既有檔案
- 新增、移除或大幅改寫階段（如 Step 3.5 Drop Zone Scan）
- 改變資料源優先序、交叉驗證規則、降級策略
- 大幅重組目錄結構（如 v1.4 的 product/ 引入）

**不寫**：
- 修錯字、調整語氣
- 補充既有文件的細節
- bug fix
- 純依賴更新

如果不確定，寫一份 1 頁的 mini-RFC 比不寫好——未來的你會感謝過去的你解釋過為什麼這樣選。

## 與其他文件的關係

- 每份 RFC 應該連結到對應的 [PRD § 章節](../PRD.md)、[CHANGELOG entry](../../CHANGELOG.md)、commit sha
- 重要 RFC 在實作後應連結到 [`perf/`](../perf/) 的實測報告
- 完整關係見 [`../README.md`](../README.md)
