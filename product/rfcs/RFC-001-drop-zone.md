# RFC-001：Drop Zone — 使用者餵資區

| 欄位 | 內容 |
|------|------|
| **狀態** | Implemented |
| **建立日期** | 2026-04-07 |
| **最後更新** | 2026-04-07 |
| **作者** | Andrew Yen |
| **對應版本** | v1.4 |
| **CHANGELOG entry** | [v1.4](../../CHANGELOG.md) |
| **PRD 章節** | [PRD § 設計原則 4](../PRD.md#4-drop-zone-優先v14-新增) |
| **相關 commit** | （待 commit 後回填） |

---

## 1. Summary

在 `input/{target}/` 開闢一個「Drop Zone」目錄，讓使用者在啟動分析前把已有的年報 PDF、商工登記截圖、LinkedIn 截圖、訪談筆記等檔案丟進去。Agent 在 Step 3.5 掃描這個目錄，把找到的檔案視為**最高優先級資料源**納入後續所有階段，但**不豁免交叉驗證規則**。

把 AI 從「不可靠的網路抓取者」轉成「可靠的資料整合者」——這是系統層級的分工明示化，也是對 AI 搜尋極限的務實回應。

## 2. Background / Problem

### 觀察到的問題

使用者（作者本人）在 2026-04-07 提出一個對「用 Claude Code 查企業資訊的極限」的系統性分析，指出在不寫主動爬蟲的前提下，AI 搜尋有五大結構性瓶頸：

1. 付費牆與深層網路阻絕（PitchBook、Bloomberg、商工進階資料）
2. WAF、Cloudflare、JS 渲染攔截 web_fetch
3. Top-N 搜尋限制、無法遞迴抓取
4. 大型 PDF / 下載類檔案處理能力有限
5. 資訊即時性與同名企業幻覺風險

使用者提出的正確洞察：**「把 AI 視為資料處理引擎而非資料庫——手動下載企業年報、直接給 Claude 解析，會比依賴它自己去網路上撈取精準且完整得多。」**

這個觀察直指系統的核心分工問題：**網路抓取是 AI 的弱項，但結構化處理是 AI 的強項**。系統如果繼續假裝自己能什麼都抓得到，就會持續消耗 token 撞牆。

### 現況的限制

在 v1.4 之前，系統處理「使用者手上已有資料」的唯一機制是 Step 4.0.5 預分析評估的**一次性 inline 詢問**：

> 「如果你已下載年報 PDF，請提供檔案路徑（如 `/Users/you/Downloads/annual-report.pdf`），可大幅提升分析品質和速度。輸入『跳過』由系統自行搜尋取得。」

這個機制有三個問題：

1. **只涵蓋年報**，不涵蓋其他高價值資料（訪談筆記、商工登記截圖、媒體剪報）
2. **只在 Step 4.0.5 出現一次**，使用者必須在那個時機點記得貼路徑
3. **路徑散落在使用者各自的下載資料夾**，沒有結構化位置，不利於多次分析或案例沉澱

## 3. Goals / Non-goals

### Goals

- G1：提供一個**結構化的檔案交接區**，使用者可以隨時把可信資料丟進去
- G2：把 drop zone 檔案納入**數據源優先序的最頂端**，高於任何 web 搜尋結果
- G3：**不破壞 v1.2 的交叉驗證安全保證**——drop zone 不算兩個來源
- G4：**不打擾無檔案的使用者**——drop zone 為空時靜默通過，不增加對話輪次
- G5：**路徑 A、路徑 B、三個 SKILL 入口都支援**，一致的使用者體驗
- G6：**隱私預設**——drop zone 內容不推上 git

### Non-goals

- 不支援自動抓取網路檔案（那是 web_fetch 的事）
- 不建構 OCR pipeline（HEIC、影像類年報的 OCR 留給未來 RFC）
- 不建構檔案版本控管（使用者自己負責檔案的時效性）
- 不試圖覆寫 v1.2 的交叉驗證——drop zone 仍算 1 個來源
- 不主動解析 Excel/CSV（Read tool 對結構化試算表支援有限）

## 4. Options Considered

### Option A：Inline 貼路徑（現況，v1.3）

保持 Step 4.0.5 的 inline 詢問機制，不做結構化目錄。

**優點**：
- 零新增檔案、零新增步驟
- 實作成本最低

**缺點**：
- 只覆蓋年報一種類型
- 只在一個階段詢問一次
- 路徑散落，無法多次複用
- 違反原則：使用者手上明明有資料，系統卻讓它「在 session 外消失」

### Option B：結構化 Drop Zone 目錄（本 RFC 選擇）

在 `input/{target}/` 建立結構化目錄，Agent 在 Step 3.5 掃描。

**優點**：
- 支援所有檔案類型（PDF、圖片、筆記、HTML）
- 所有階段都能存取
- 使用者可以多次分析同一家公司時重用
- 與案例沉澱機制協同
- 把「手動餵資」這個根本洞察明示化為系統設計

**缺點**：
- 需要新增 1 個階段（Step 3.5）
- 需要使用者理解目錄結構
- 增加 token 預載（掃描結果要進 context）
- 需要明確界定「drop zone 檔案是否豁免交叉驗證」的規則

### Option C：MCP 檔案伺服器

部署一個 MCP server 動態接收使用者上傳，讓 Claude Code 以 tool call 方式存取。

**優點**：
- 最靈活
- 可以支援檔案版本控制、multi-tenant

**缺點**：
- 超過這個專案的複雜度預算
- 使用者需要配置 MCP，大幅提高進入門檻
- 違反「終端友善、零依賴」的設計取向
- 不解決「使用者還是要知道檔案路徑」的問題，只是把問題移到另一個地方

## 5. Decision

**選擇**：Option B（結構化 Drop Zone 目錄）

**理由**：

- B 直接解決了原則層級的問題（把 AI 的分工從「抓取」轉為「整合」），A 只是現況的小修補，C 超過複雜度預算。
- B 的代價主要是**文件與流程的設計成本**，而不是執行時的 token 成本（掃描動作本身便宜）。
- B 的命名空間（`input/{target}/`）天然支援多目標、多次分析、跨 session 的資料復用，這是 A 做不到的。
- 隱私風險可以用 `.gitignore` 排除 `input/*/` 解決，成本很低。

### 關鍵決策點

這三個子決策在實作前與使用者單獨確認過：

| 決策 | 選擇 | 原因 |
|------|------|------|
| 目錄 slug 命名 | 中文原樣（`input/個人理財 SaaS A/`） | 使用者直覺優先；macOS/Linux/Read 工具對中文路徑都沒有實際問題 |
| Drop zone 檔案是否能單獨滿足交叉驗證 | **不能**，算 1 個來源 | 防止使用者上傳過時/錯誤截圖直接污染報告，v1.2 的安全保證不能因為來源是「使用者提供」就放寬 |
| MANIFEST.md 強制 vs 選用 | **選用** | 降低摩擦；沒有 MANIFEST 時用檔名 + PDF 第一頁推測，模糊時主動問一次 |

## 6. 效能影響

### 設計時預估

| 維度 | 變更前 | 變更後 | Δ |
|------|--------|--------|---|
| 預載 token（系統 prompt + skill + agent） | ~2,400 | ~2,700 | +300（新 Step 3.5 + drop-zone.md 指向） |
| 平均階段新增 Read 呼叫 | — | +1–2（掃描時讀 MANIFEST + 小 .md 筆記） | — |
| 平均階段新增 Glob 呼叫 | — | +1（Step 3.5 掃描目錄） | — |
| 預期搜尋次數變化（有年報時） | 大型 40–55 | 大型 35–48 | −5 to −7 |
| 預期 fetch 次數變化（有年報時） | 大型 8–12 | 大型 6–9 | −2 to −3 |
| 命中率預期變化 | baseline 待定 | 使用者有餵資時顯著提升 | 視 Drop Zone 使用率而定 |
| 證據等級分布預期變化 | — | `[資料缺失]` 比例下降；`[部分證據]` 在無 web 佐證時增加 | 淨效果：報告完整性提升 |

> **命中率定義**：被報告引用 / 直接導致下一步驗證的搜尋呼叫數 ÷ 總搜尋呼叫數。完整定義見 [`product/perf/README.md`](../perf/README.md)。

### 實測結果

> **待回填**。首次跑有 Drop Zone 的真實案例後填寫。

| 維度 | 預估 | 實測 | 偏差 | 備註 |
|------|------|------|------|------|
| | | | | |

**測試案例**：待定（建議：重跑個人理財 SaaS A，比較 v1.1 baseline 與 v1.4 + drop zone 的差異）
**測試日期**：TBD
**對照 baseline**：[baseline-v1.1-token-usage.md](../perf/baseline-v1.1-token-usage.md)

## 7. 風險

| 風險 | 嚴重度 | 緩解方式 |
|------|--------|---------|
| 使用者上傳過時或偽造的截圖污染報告 | 高 | 交叉驗證規則不豁免；drop zone 檔案算 1 個來源，關鍵欄位仍須 web 佐證 |
| 中文路徑在某些外部工具出問題 | 低 | 當前所有使用的工具（Read、Glob、Bash）都支援；有問題時使用者可自行改英文 slug |
| Drop zone 內容太大塞爆 context | 中 | Step 3.5 只預讀 MANIFEST + 小 .md 筆記（<50KB），PDF/圖片延後讀 |
| 使用者忘記 drop zone 存在，持續付出 web 搜尋成本 | 中 | README 在使用者面向的位置；預分析評估的年報取得提示會點出「可放入 input/」 |
| Drop zone 資料洩漏到 git | 高 | `.gitignore` 排除 `input/*/`，只有 README 和 .gitkeep 被 tracked |

## 8. Implementation Plan

### 已新增的檔案

- `input/.gitkeep` — 保留目錄
- `input/README.md` — 使用者面向的使用說明
- `references/methodology/drop-zone.md` — Agent 處理規範（資料源優先序、掃描時機、檔案類型推測啟發式、交叉驗證規則、引用格式、年報整合邏輯、安全注意事項）

### 已修改的檔案

- `.gitignore` — 加入 `input/*/` 排除規則
- `agent/AGENT-CORE.md` — 數據源優先序最前面加入「使用者提供文件（input/）」，並指向 drop-zone.md
- `.claude/skills/recon/SKILL.md` — 新增 **Step 3.5: Drop Zone Scan**；更新 Step 4.0.5 讓年報路徑邏輯先檢查 drop zone
- `.claude/skills/company/SKILL.md` — 加入 Step 4 (Drop Zone Scan)，原步驟順延
- `.claude/skills/industry/SKILL.md` — 同上
- `.claude/rules/output-quality.md` — 加入 drop zone 引用格式、降一級規則、metadata 紀錄要求

### 不動的檔案

- 各階段 prompt（entity-verification、annual-report-analysis、stakeholder-investigation 等）— 透過 AGENT-CORE.md 的優先序規則繼承，無需個別改

## 9. Followups / Open Questions

- **F1**：首次跑有 drop zone 的真實案例後回填本 RFC §6「實測結果」
- **F2**：觀察使用者實際使用模式：是否記得把檔案放進去？是否會用 MANIFEST？
- **F3**：是否需要支援**跨目標共用**的 drop zone？（例如產業分析時一份 IEK 報告可套用到多家公司）目前設計是「每個目標一個目錄」，重複檔案需要複製。如果使用頻繁再考慮 `input/_shared/` 機制。
- **F4**：Drop Zone 的存在是否應該在 README.md 的顯眼位置說明，避免使用者漏看？
- **F5**：PDF 第一頁推測檔案類型的啟發式需要實測調整
- **F6**：`[使用者提供，無公開佐證]` 這個證據等級尚未正式寫入 `output-quality.md` 的四級標記，v1.4 用「降一級」的方式處理，未來是否要升格為正式的第五級？

## 10. References

- 原始對話：使用者 2026-04-07 提出「AI 搜尋企業資訊的極限」分析，五點限制 + 「手動餵資取代自動搜尋」洞察
- 相關方法論：[`references/methodology/drop-zone.md`](../../references/methodology/drop-zone.md)
- 相關原則：[`product/PRD.md § 設計原則 4`](../PRD.md#4-drop-zone-優先v14-新增)
- 歷史對照：v1.2 交叉驗證規則（`references/methodology/fetch-policy.md`「台灣公司登記」章節）
