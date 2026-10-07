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
| 1 | costring | `costring.com/business/[統編]/` | web_fetch | **微型廣告代理 D 案實測：fetch 成功率高，欄位完整**（代表人、董監事+持股、實收資本、設立日、最後核准變更日、地址、營業項目）。MCP 全程逾時時的主力回退源 |
| 1 | 公司登記查詢台灣 | `companys.com.tw/[統編]` | web_fetch | 微型廣告代理 D 案實測：fetch 成功、欄位與 costring 一致，可作交叉比對的第二獨立源 |
| 1 | TechNews 公司資料 | `info.technews.tw/company/[統編]` | web_fetch | 上市遊戲營運商 C 案：資料最新、成功率高。⚠️ **但微型廣告代理 D 案對微型公司回傳 404（未被索引）**——大公司優先，微型直接改用 costring/companys |
| 1 | INDEX 公司登記 | `biz.news.org.tw/company_[統編]` | web_fetch（⚠️ 首次 fetch 可能 301 redirect，需 follow） | 有「最後核准變更日期」欄位；⚠️ 部分欄位 JS 動態載入，fetch 可能回傳不完整（上市遊戲營運商 C 案），失敗即換源不重試 |
| 2 | 台灣公司網 | `twincn.com/item.aspx?no=[統編]` | web_search snippet only（在黑名單上） | 董監事名單常比其他來源更新，snippet 中可讀 |
| 3 | OpenGovTW | `opengovtw.com/ban/[統編]` | web_fetch | ⚠️ 資料可能過時，**禁止作為唯一來源** |

### 已知教訓

- opengovtw.com 曾發生董監事名單和資本額與商工署不同步的情況（個人理財 SaaS A 案，本地案例檔不入庫；[董事 A-1]/[董事 A-2] vs [董事 A-3]/[董事 A-4]差異、實收資本額 [實收資本額 X] vs [實收資本額 Y]差異）
- **規則**：登記資料（董監事、資本額、地址）至少兩個獨立來源比對一致才可寫入報告；若來源間有衝突，以「最後核准變更日期」最新者為準
- **資安廠商自家官網通常 fetch 失敗**（雲端資安代理商 B 案：自家 WAF 對自動化請求一律擋）。遇到資安/CDN 代理商，**預期**官網 403，直接走媒體報導 + snippet，不浪費 fetch 預算
- **MCP `tw-data`（tw_company_lookup / tw_person_network）可能整 session 逾時不可用**（微型廣告代理 D 案：4 次呼叫全部 30s timeout）。**不要連試超過 2 次**，立即改走 web 回退鏈：登記資料→`costring.com/business/[統編]/` + `companys.com.tw/[統編]`（兩源交叉）；人物關聯法人→`data.zhupiter.com/oddt/[id]/[人名]/`（見 deep-dive-sources.md）
- **司法院裁判書 PDF**：搜尋結果給的 `judgment.judicial.gov.tw/FILES/{法院代碼}/{年度,字別,號,日期,序}.pdf` 對程式抓取回傳 HTML 而非 PDF。改用 `data.judicial.gov.tw/opendl/JDocFile/{同一段路徑}.pdf` 可直接取得 PDF 並抽出全文（企業 XR 軟體 F 案實測）。搜尋結果常混入同字別、不相關當事人的裁判書，抽出全文後須先核對當事人欄位再採用
- **twfile.com 的人物查詢頁 `Lp.aspx?q=[人名]` 與公司情報頁同為 JS 渲染，fetch 回傳空白**（已在黑名單，此處補記人物頁 URL 形式）

**維護規則**：每次分析中遇到新的 fetch 失敗網站，在案例沉澱（`cases/{target}/case-log.md`）中記錄，定期更新此黑名單。

## 降級規則

以下場景應快速降級，避免浪費搜尋次數：

### 監察人 / 非執行董事
- 1 次 web_search 無果 → 標註 `[資料缺失，合規角色]` 後停止追蹤
- 理由：台灣中小企業的監察人多為合規性質，公開資訊極少。每多搜一次的邊際資訊增益趨近於零

### 非上市公司營收數據
- 1 次 web_search 無果 → 直接標註 `[資料缺失]`，不重複搜尋
- 理由：非上市公司財報不公開，搜尋「XX 公司 營收」永遠不會有結果。改用現金流結構分析

### 微型企業員工數
- 1 次 web_search 無果 → 標註 `[資料缺失]`，改用間接推估（資本額 + 產品線 + 徵才狀態）
- 理由：微型企業極少在求職平台填寫團隊規模，LinkedIn 有登入牆——這是 OSINT 盲區（個人理財 SaaS A 案：104/Cake/Yourator/meet.jobs 全部無此欄位），重複搜尋的邊際增益為零

### 同名但無關的搜尋結果
- 若搜尋人名出現明顯不相關的同名者（如政治人物、學者），不追蹤。只追蹤與目標公司或其產業有明確關聯的結果
