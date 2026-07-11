# Web Fetch 政策（Fetch Policy）

## 黑名單

以下網站因 JavaScript 渲染或登入牆，web_fetch 必定失敗。遇到這些網站時，**直接依賴 web_search snippet 取得資訊，不執行 web_fetch**。

| 網站 | 類型 | 原因 | MCP 替代（v1.8） |
|------|------|------|-----------------|
| twincn.com | 台灣公司登記 | JS 渲染，fetch 回傳空白 | `tw_company_lookup` / `tw_person_network` |
| twfile.com | 台灣公司情報 | JS 渲染，fetch 回傳空白 | `tw_company_lookup`（資料重複） |
| 104.com.tw | 求職平台 | JS 渲染（Vite SPA），fetch 只取得載入腳本 | `headless_fetch` |
| findcompany.com.tw | 公司登記查詢 | 403 Forbidden | `tw_company_lookup`（findbiz 官方源更佳） |
| linkedin.com | 職業社群 | 登入牆，fetch 無法取得內容 | 無（登入牆非 JS 問題，MCP 也無法突破） |
| alphaloan.co | 公司資訊 | 410 Gone | 無（站點已關閉） |

> **MCP 工具可用時**：標有 MCP 替代的站點，優先使用對應 MCP 工具而非 search snippet。MCP 不可用時仍依照上述黑名單規則處理。

## 台灣公司登記：推薦來源與比對規則

> 完整比對流程見 `agent/prompts/entity-verification.md`「台灣公司登記資料：多來源交叉比對」章節。

### 來源優先序

| 優先序 | 網站 | URL 格式 | 取得方式 | 備註 |
|--------|------|---------|---------|------|
| 1 | INDEX 公司登記 | `biz.news.org.tw/company_[統編]` | web_fetch（⚠️ 首次 fetch 可能 301 redirect，需 follow） | 有「最後核准變更日期」欄位，更新較即時 |
| 2 | 台灣公司網 | `twincn.com/item.aspx?no=[統編]` | web_search snippet only（在黑名單上） | 董監事名單常比其他來源更新，snippet 中可讀 |
| 3 | OpenGovTW | `opengovtw.com/ban/[統編]` | web_fetch | ⚠️ 資料可能過時，**禁止作為唯一來源** |

### 已知教訓

- opengovtw.com 曾發生董監事名單和資本額與商工署不同步的情況（見 `references/cases/case-個人理財 SaaS A.md`，[董事 A-1]/[董事 A-2] vs [董事 A-3]/[董事 A-4]差異、實收資本額 [實收資本額 X] vs [實收資本額 Y]差異）
- **規則**：登記資料（董監事、資本額、地址）至少兩個獨立來源比對一致才可寫入報告；若來源間有衝突，以「最後核准變更日期」最新者為準

**維護規則**：每次分析中遇到新的 fetch 失敗網站，在案例沉澱（`cases/{target}/case-log.md`）中記錄，定期更新此黑名單。

## 降級規則

以下場景應快速降級，避免浪費搜尋次數：

### 監察人 / 非執行董事
- 1 次 web_search 無果 → 標註 `[資料缺失，合規角色]` 後停止追蹤
- 理由：台灣中小企業的監察人多為合規性質，公開資訊極少。每多搜一次的邊際資訊增益趨近於零

### 非上市公司營收數據
- 1 次 web_search 無果 → 直接標註 `[資料缺失]`，不重複搜尋
- 理由：非上市公司財報不公開，搜尋「XX 公司 營收」永遠不會有結果。改用現金流結構分析

### 同名但無關的搜尋結果
- 若搜尋人名出現明顯不相關的同名者（如政治人物、學者），不追蹤。只追蹤與目標公司或其產業有明確關聯的結果
