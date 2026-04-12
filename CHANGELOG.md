# Changelog

所有版本變更紀錄。格式參考 [Keep a Changelog](https://keepachangelog.com/)。

> v1.4 起，每次有意義的設計變更都有對應的 RFC，位於 `product/rfcs/`。CHANGELOG 保留 user-facing release notes 的視角，engineering 視角的決策過程請見 RFC。

## [v1.6] — 2026-04-12

新增 **Cases Registry**——CRM 式企業分類 DB + 同步腳本。解決 case 累積後缺乏跨案例索引、分類、篩選機制的問題。每次分析完成後跑 `sync`，自動從報告提取 metadata 並維護結構化企業目錄。

### 新增

- **`cases/_registry.json` — 結構化企業 DB**
  - 參考 HubSpot / Salesforce CRM 分類維度設計
  - 每家公司記錄：基本資訊、產業分類（雙層：sector + industry）、規模、上市狀態、地理、分析狀態、風險評估、財務快照
  - Sector 大類（8 個，GICS 簡化）：科技 / 金融 / 娛樂 / 製造 / 零售 / 醫療 / 能源 / 服務
  - Risk level（4 級）：critical / high / medium / low
  - 手動 enrichment 不會被 auto-sync 覆蓋（merge 策略：scan 只填空值 + 更新追蹤欄位）

- **`cases/_index.md` — 人類可讀索引**
  - 從 `_registry.json` 自動生成
  - 三個視角：總覽表、按產業分類、按規模分類
  - 含風險 emoji 標記（🔴🟠🟡🟢）和一句話判斷

- **`scripts/sync-registry.py` — 同步腳本**
  - Python 3 標準庫，零依賴
  - `sync`：掃描所有 `cases/*/` → 解析報告 metadata（處理 3 種格式）→ 更新 registry → 生成 index
  - `show`：終端機印出企業摘要表
  - `show --sector / --size / --risk`：篩選功能
  - 首次建立時預填充 5 家已分析企業

### 修改

- **`.gitignore`**：新增 `cases/_registry.json` 和 `cases/_index.md`（含機敏摘要，不入 git）

### 設計決策

| 決策 | 選擇 | 原因 |
|------|------|------|
| DB 格式 | JSON（而非 SQLite / YAML） | 人類可讀、Claude 可直接 Read/Write、標準庫即可處理 |
| 索引位置 | `cases/` 根層（而非 `product/` 或獨立 `db/`） | 與 case 資料同層、同 gitignore 規則 |
| Merge 策略 | scan 只填空值 + 追蹤欄位 always update | 手動 enrichment（sector、risk、verdict）不被覆蓋 |
| 腳本位置 | `scripts/`（新目錄） | 與 agent/、cases/ 平行，職責清楚 |
| Sector 分類 | 8 個大類 | 足夠區分但不過度細分，可用 industry 欄位補足細項 |

## [v1.5] — 2026-04-10

三大變更：**統一 `cases/` 目錄**（取代 `input/` + `output/` + `references/cases/` 三散結構）、新增 **`/supplement` 增量更新機制**（分析完成後追加新資料不需重跑全流程）、新增**訪談筆記結構化 Schema**（讓 Agent 根據 confidence 等級自動判斷證據處理方式）。

### 新增

- **`cases/` 統一目錄**（詳見 [RFC-003](product/rfc/RFC-003-cases-and-supplement.md)）
  - 每家公司/產業一個資料夾：`cases/{目標名稱}/`
  - 內含 `input/`（drop zone）、`company-report.md`（含 Version History）、`decision-brief.md`、`supplements/`（增量 memos）、`case-log.md`
  - `ls cases/` 一眼看到所有分析過的目標
  - `cases/*/` 被 gitignore 排除，`cases/README.md` 和 `cases/_case-template.md` 已 tracked

- **`/supplement` Skill — 增量更新**
  - 讀取既有報告 + 新 drop zone 檔案 → 產出 Supplement Memo + 更新報告 Version History
  - 搜尋預算 5 search / 2 fetch（不重跑全流程）
  - 三類發現：新發現、衝突、證據等級變動
  - 可選：同時重新產出 Decision Brief（零搜尋預算）

- **Version History（版本鏈）**
  - 報告 metadata 追蹤版本歷程：v1.0 → v1.1 → v1.2...
  - `/supplement` 執行時自動追加新行，不修改主報告正文

- **訪談筆記結構化 Schema**（`references/methodology/interview-notes-schema.md`）
  - YAML frontmatter 定義 `type`、`source`、`confidence`
  - Agent 根據 confidence 等級（low/medium/high）自動決定證據處理方式

### 搬移

- `output/*.md` → `cases/{目標名稱}/`（報告進入統一目錄）
- `references/cases/case-*.md` → `cases/{目標名稱}/case-log.md`（案例沉澱進入統一目錄）
- `references/cases/_case-template.md` → `cases/_case-template.md`

### 修改

- **`.gitignore`**：新增 `cases/*/` 取代 `input/*/` + `output/*.md` + `references/cases/case-*.md`
- **`CLAUDE.md`**：更新專案結構 + 新增 `/supplement` 使用說明
- **`agent/AGENT-CORE.md`**：`input/{target}/` → `cases/{target}/input/`
- **`.claude/skills/recon/SKILL.md`**：Step 3.5/4/6 路徑更新 + Step 6 加 supplement 提示
- **`.claude/skills/company/SKILL.md`、`industry/SKILL.md`**：drop zone 路徑更新
- **`references/methodology/drop-zone.md`**：全部路徑更新
- **`.claude/rules/output-quality.md`**：路徑更新 + report-type 加 `supplement`
- **`references/templates/company-report.md`**：加 Version History 區塊
- **`input/README.md`**：改為 redirect 提示，指向 `cases/README.md`
- **`README.md`**：專案結構、產出、案例學習段落全面更新
- **`product/architecture.md`**：架構圖、案例層、settings 段落更新
- **`product/flow-diagram.md`**：Mermaid 圖更新（output → cases）
- **`product/PRD.md`**：數據源優先序路徑 + 系統概覽圖更新
- **`references/methodology/fetch-policy.md`**：案例沉澱路徑更新

### 設計決策

| 決策 | 選擇 | 原因 |
|------|------|------|
| 目錄結構 | 合併 `cases/`（而非 input+output 分開） | 使用者直覺，一個 `ls` 看全貌 |
| 增量更新 | `/supplement`（而非全量重跑） | 節省 20+ 分鐘和搜尋預算 |
| 版本控制 | 版本鏈（而非多檔案） | 主報告不分裂，supplement memo 獨立追蹤 |
| 訪談筆記 | 結構化 schema（而非 free-form） | 讓 agent 自動判斷 confidence → 證據等級 |
| 適用範圍 | 通用化（所有 `/company` 和 `/industry`） | 非一次性需求 |
| 主報告是否被修改 | 不修改正文，只改 Version History | 保持原版完整性，增量內容獨立在 supplement memo |

## [v1.4] — 2026-04-07

兩大變更：引入 **Drop Zone**（使用者餵資區）把 AI 從「不可靠的抓取者」轉成「可靠的整合者」；新增 **product/** 目錄建立 PM 工件層（PRD、RFC、效能追蹤），讓迭代過程本身可審視。

### 新增

- **Drop Zone — `input/{target}/`**（詳見 [RFC-001](product/rfcs/RFC-001-drop-zone.md)）
  - 使用者可預先把年報 PDF、商工登記截圖、LinkedIn 截圖、訪談筆記丟入 `input/{目標名稱}/`
  - Agent 在新增的 **Step 3.5: Drop Zone Scan** 掃描該目錄，把檔案視為最高優先級資料源納入後續所有階段
  - **不豁免交叉驗證**：drop zone 檔案算 1 個來源，關鍵欄位仍須 web 佐證（保留 v1.2 安全保證）
  - 隱私預設：`input/*/` 被 gitignore 排除
  - 對應方法論：`references/methodology/drop-zone.md`

- **PM 工件層 — `product/` 目錄**
  - `product/PRD.md`：主 PRD，首次撰寫，回溯 v1.0–v1.4 設計脈絡
  - `product/rfcs/`：設計變更紀錄目錄，含模板、索引、RFC-001
  - `product/perf/`：效能追蹤目錄，含方法論、命中率定義、baseline 報告

### 搬移

- `docs/architecture.md` → `product/architecture.md`（git mv，history 保留）
- `docs/design-rationale.md` → `product/design-rationale.md`
- `docs/flow-diagram.md` → `product/flow-diagram.md`
- `references/cases/case-個人理財 SaaS A-token-usage-report.md` → `product/perf/baseline-v1.1-token-usage.md`（原檔 gitignored，移動後加入 tracking）
- `references/cases/case-個人理財 SaaS A-model-comparison.md` → `product/perf/baseline-v1.1-model-comparison.md`

### 修改

- **`agent/AGENT-CORE.md`**：數據源優先序最前面加入「使用者提供文件（input/）」；警告句從「不要載入 docs/」改為「不要載入 product/」
- **`.claude/skills/recon/SKILL.md`**：新增 Step 3.5 Drop Zone Scan；更新 Step 4.0.5 讓年報路徑邏輯先檢查 drop zone；更新 model-comparison 路徑引用
- **`.claude/skills/company/SKILL.md`、`industry/SKILL.md`**：加入 Drop Zone Scan 階段
- **`.claude/rules/output-quality.md`**：加入 drop zone 引用格式 `[來源: input/{target}/{filename}]`、降一級規則、metadata 紀錄要求；順手修正 `[部分證據]` 的破損字元
- **`.gitignore`**：新增 `input/*/` 排除規則
- **`CLAUDE.md`**：更新專案結構描述，加入 `input/` 和 `product/` 說明
- **`README.md`**：專案結構樹更新；所有 `docs/` 路徑引用改為 `product/`

### 設計決策

| 決策 | 選擇 | 原因 |
|------|------|------|
| Drop zone 檔案是否豁免交叉驗證 | 不豁免（算 1 個來源） | 防止過時截圖污染報告，v1.2 的安全保證不因來源類型放寬 |
| 目錄 slug 命名 | 中文原樣 | 使用者直覺優先；macOS/Linux 支援無問題 |
| MANIFEST.md 強制 vs 選用 | 選用 | 降低摩擦；模糊時 agent 問一次 |
| PM 工件層位置 | 新開 `product/` 而非擴張 `docs/` | 工件集中、對作品集讀者清楚；git history 接受短期雜訊 |
| RFC 格式 vs ADR | RFC（含效能預估/實測） | 決策過程比架構記錄更重要；效能追蹤內建 |
| CHANGELOG 與 RFC 的分工 | 共存，CHANGELOG = user-facing，RFC = engineering 視角 | 功能不重疊 |
| Perf baseline 策略 | 沿用 v1.1 個人理財 SaaS A案報告 | 避免重建 baseline 的額外成本 |
| v1.0–v1.3 是否追溯補 RFC | 不補 | 避免考古成本；歷史決策保留在 CHANGELOG |

## [v1.3] — 2026-04-07

上市遊戲營運商 C（大型上市公司）分析案例暴露系統性缺口：年報 PDF 是 must have 但未強制、營收結構被誤判（90%→實際 74%）、無預分析成本評估。本版新增「預分析評估」和「年報解析」兩大機制，確保不同規模公司獲得一致品質的分析。

### 新增

- **`agent/prompts/annual-report-analysis.md`**：年報解析階段 prompt
  - 12 項必須提取的數據點（營收拆分、供應商集中度、重大合約等）
  - PDF 取得降級鏈（使用者提供 > IR 網站 > 監管平台 > HTML 版）
  - 強制產出「衝突清單」校正先前搜尋誤差
  - 適用矩陣：大型=強制、中型=建議、微型=跳過

- **`references/methodology/annual-report-sources.md`**：各市場年報來源登記表
  - 涵蓋台灣（MOPS/IR）、美國（EDGAR）、日本（EDINET）、韓國（DART）、香港（HKEXnews）、中國（巨潮）
  - 台灣年報標準結構和關鍵頁面定位提示
  - 通用搜尋模式和已知限制

- **預分析評估（Pre-Analysis Assessment）**：插入 `recon/SKILL.md` Step 4.0.5
  - entity-verification 完成後、stakeholder-investigation 之前
  - 零搜尋預算，向使用者展示：資料豐富度、年報計畫、搜尋預估、模型建議、時間預估
  - 使用者確認後才繼續，確保知情決策

### 修改

- **`agent/AGENT-ROUTES.md`**：路徑 B 新增 Step 2.5（年報解析）和預分析評估檢查點

- **`agent/AGENT-CORE.md`**：
  - 核心原則新增「絕對誠實」條款——找不到就標 `[資料缺失]`，不以猜測填補
  - 核心原則新增「數據源優先序」——年報 > IR 網站 > 財經平台 > 新聞 > snippet
  - 搜尋預算表新增「年報解析」行（5 search + 3 fetch）

- **`agent/prompts/company-deep-dive.md`**：新增「年報數據前置檢查」
  - 大型/上市未取得年報 → 6 個維度自動降級標註
  - 報告 metadata 標註警告

- **`.claude/skills/recon/SKILL.md`**：插入 Step 4.0.5（預分析評估）和 Step 4.2.5（年報解析觸發）

- **`.claude/skills/company/SKILL.md`**：對齊 recon 的預分析評估和年報解析流程

- **`references/methodology/scale-classification.md`**：新增「強制數據源」欄位
  - 大型/上市 = 商業登記 + 年報（強制）+ 財經平台

- **`references/methodology/quality-checklist.md`**：新增 6 項
  - #8.5-8.8：年報數據檢查（取得、營收來源、重大合約、衝突校正）
  - #23-24：預分析評估回顧（預估準確度、模型適配）

- **`references/cases/_case-template.md`**：新增「預分析評估回顧」區塊（預估 vs 實際對照表）

### 設計決策

| 決策 | 選擇 | 原因 |
|------|------|------|
| 年報階段放在 Step 2.5 | 產業分析之後、公司深度之前 | company-deep-dive 是最需要年報數據的階段，年報摘要作為即時 context 直接銜接 |
| 預分析評估放在 Skill 層 | 非 Agent 階段，零搜尋預算 | 這是流程控制決策，不是研究執行，不需要搜尋 |
| 模型建議是「資訊性」 | 不強制切換，僅告知使用者 | 無法 mid-session 切換模型；clone 使用者需要在開始前知道最佳配置 |
| 年報降級標註而非阻斷 | 允許無年報繼續分析，但降級 | 使用者可能有正當理由跳過（如 PDF 取得失敗），不應阻斷整個流程 |

## [v1.2] — 2026-04-06

修正台灣公司登記資料引用流程——單一來源（opengovtw）曾導致董監事名單和資本額寫入過時資料，現在強制多來源交叉比對。

### 修正

- **entity-verification.md**：新增「台灣公司登記資料：多來源交叉比對（強制）」章節
  - 來源優先序：biz.news.org.tw > twincn.com snippet > opengovtw.com
  - 5 步比對流程，禁止單一來源直接寫入報告
  - 完成標準新增 2 條：多來源交叉比對 + 資料截至日期標註

- **quality-checklist.md**：新增「法律實體資料正確性」檢查區塊（#7-#8）
  - #7 登記資料交叉比對（含常見錯誤示例與正確做法）
  - #8 資料時效標註（截至最後核准變更日期，非查詢日）
  - 後續項目重新編號（原 7-20 → 9-22）

- **fetch-policy.md**：新增「台灣公司登記：推薦來源與比對規則」章節
  - 來源優先序表（含 URL 格式、取得方式、redirect 提醒）
  - 已知教訓段落，引用具體案例

- **.gitignore**：新增 `references/cases/case-*.md` 和 `output/*.md`，避免公司特定分析結果推上 public repo

## [v1.1] — 2026-04-06

新增 User Profile 與 Decision Brief 機制：從「給你資訊」進化到「告訴你這對你意味著什麼」。

### 新增

- **User Profile（使用者設定檔）**
  - 首次使用任何 Skill 時觸發 onboarding（1 輪 4 題，可跳過）
  - 儲存角色、產業背景、決策情境、特殊關注
  - 支援「更新我的 profile」隨時修改
  - 檔案位於 `.claude/user-profile.md`，已加入 .gitignore

- **Decision Brief（決策簡報）**
  - 品質 Review 後的新階段，基於完成的報告 + User Profile 產出
  - 五種角色鏡頭：投資人 / 求職者 / 合作夥伴 / 競品分析師 / 其他
  - 六段結構：一句話判斷、三件重要的事、紅旗警示、特殊關注回應、該問的問題、下一步行動
  - 零搜尋預算，完全基於已有報告重新解讀
  - 證據等級從主報告繼承，不升級不降級

### 修改

- `agent/AGENT-ROUTES.md`：兩條路徑各新增 Decision Brief 階段
- `.claude/skills/recon/SKILL.md`：新增 Step 0（profile 檢查）、Step 5.5（Decision Brief）
- `.claude/skills/company/SKILL.md`、`industry/SKILL.md`：同步新增 Step 0 和 Decision Brief
- `.claude/rules/output-quality.md`：新增 `decision-brief` report-type 和特殊規則
- `references/methodology/quality-checklist.md`：新增 5 項 Decision Brief 檢查項目
- `.claude/settings.json`：新增 user-profile.md 讀寫權限
- `CLAUDE.md`、`docs/architecture.md`：同步更新流程圖和結構說明

## [v1.0] — 2026-04-06

首次公開版本。完整的產業與公司情報研究工作流。

### 系統架構
- Skill / Agent / Reference 三層分離架構
- 三個入口指令：`/recon`（統一入口）、`/industry`（產業分析）、`/company`（公司分析）
- Agent 自主執行迴圈：搜尋 → 驗證 → 交叉比對 → 結構化產出

### 研究能力
- 路徑 A：產業 → 公司（宏觀到微觀）
- 路徑 B：公司 → 產業（以公司為錨點的產業分析）
- 規模自適應：微型 / 中型 / 大型上市公司自動切換分析框架
- 四級證據標記：充分證據 / 部分證據 / 推測待驗證 / 資料缺失

### 執行層
- AGENT-CORE：角色定義、迴圈邏輯、token 預算、降級策略、錯誤處理
- AGENT-ROUTES：路徑與階段清單
- 四個階段 prompt：實體驗證、利害關係人調查、產業分析、公司深度分析

### 知識層
- 方法論：路徑選擇、規模分類、品質檢查、產業特定來源策略、fetch 政策
- 報告模板：產業報告、公司報告
- 案例沉澱機制與標準模板

### 品質控制
- Rules 自動生效（output-quality.md）
- 報告檔名規範、來源追蹤、證據等級標記、語言規範
