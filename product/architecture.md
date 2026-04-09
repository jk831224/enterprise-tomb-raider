# Enterprise Tomb Raider — 系統架構文件

> 最後更新：2026-04-10（v1.5）

## 系統定位

Enterprise Tomb Raider（企業祖墳探勘器）是一套基於 Claude 的產業與公司情報研究系統，將「對話引導」與「自主研究」拆成兩個獨立的執行層，透過結構化參數傳遞串接。

**一句話架構**：使用者透過 `/recon` 指令啟動 → Skill 層釐清需求 + 預分析評估 → Agent 層自主執行多階段研究（含年報解析）→ 結構化報告產出到 `cases/{目標}/` → 後續可用 `/supplement` 增量更新。

**入口**：透過 `.claude/skills/` 定義的 `/recon`、`/industry`、`/company`、`/supplement` 指令觸發。

> 完整流程圖見 [`flow-diagram.md`](flow-diagram.md)（Mermaid 格式，可視化渲染）。

---

## 架構總覽

```
┌─────────────────────────────────────────────────────┐
│                      使 用 者                        │
│         /recon  ·  /industry  ·  /company            │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              .claude/skills/ (入口層)                 │
│                                                     │
│  ・需求界定（Scoping）                                │
│  ・路徑選擇（A: 產業→公司 / B: 公司→產業）            │
│  ・預分析評估（v1.3 新增：資源預估 + 模型建議）         │
│  ・流程控制（按階段載入 prompt、階段轉換）              │
│  ・品質 Review                                       │
└────────────────────────┬────────────────────────────┘
                         │ 載入 AGENT-CORE.md + 階段 prompt
                         ▼
┌─────────────────────────────────────────────────────┐
│              agent/ (執行層)                          │
│                                                     │
│  ・自主搜尋迴圈（web_search + web_fetch）              │
│  ・交叉驗證                                          │
│  ・年報解析（v1.3 新增：大型/上市強制）                 │
│  ・降級策略                                          │
│  ・結構化產出                                         │
└────────────────────────┬────────────────────────────┘
                         │ 引用
                         ▼
┌─────────────────────────────────────────────────────┐
│              references/ (知識層)                     │
│                                                     │
│  ・methodology/  方法論（含年報來源、訪談筆記 schema）   │
│  ・templates/    報告模板（含 supplement-memo）         │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│              cases/{目標}/ (案例統一目錄，v1.5)         │
│                                                     │
│  ・input/         Drop Zone（使用者餵資）               │
│  ・company-report.md  主報告（含 Version History）      │
│  ・decision-brief.md  決策簡報                         │
│  ・supplements/   增量更新 Memos（/supplement 產出）     │
│  ・case-log.md    案例沉澱                             │
│                                                     │
│  品質約束：.claude/rules/output-quality.md              │
└─────────────────────────────────────────────────────┘
```

---

## 職責切割

### 入口層（Skills）

**檔案**：`.claude/skills/{recon,industry,company,supplement}/SKILL.md`

| 職責 | 說明 |
|------|------|
| 需求界定 | 判斷路徑 A（產業→公司）或路徑 B（公司→產業） |
| Scoping | 引導使用者釐清細分領域、地理範圍、分析目的 |
| 規模預判 | 依標準將目標分類為微型/中型/大型，決定分析策略 |
| **預分析評估** | **（v1.3）** entity-verification 完成後，向使用者展示資源預估、模型建議、年報計畫。零搜尋預算，等待使用者確認後才繼續 |
| 流程控制 | 按階段載入 AGENT-CORE.md 和對應 prompt，驅動研究執行 |
| 階段轉換 | 各階段產出後，引導使用者確認並決定下一步 |
| 品質 Review | 用 quality-checklist.md 檢視最終報告 |

### 執行層（Agent）

**檔案**：`agent/AGENT-CORE.md` + `agent/prompts/*.md`（動態載入）

| 職責 | 說明 |
|------|------|
| 接收參數 | 從 Skill 層接收結構化輸入 |
| 多階段研究 | 依序執行：實體驗證 → 利害關係人調查 → 產業分析 → **年報解析** → 公司深度分析 |
| 自主搜尋迴圈 | 每階段內部執行「搜尋→評估→補充搜尋」迴圈直到滿足產出標準 |
| 降級處理 | 搜尋上限內無法滿足標準時，標註證據等級後降級產出 |
| 結構化產出 | 依 templates/ 格式產出報告 |

**關鍵機制：Prompt 動態載入**
Agent 不一次載入所有階段 prompt。進入每個階段時才載入對應的 `prompts/*.md`，減少 context window 消耗。

```
agent/prompts/
├── entity-verification.md        # 法律實體驗證（路徑 B Step 1）
├── stakeholder-investigation.md  # 利害關係人調查（路徑 B Step 1.5）
├── industry-analysis.md          # 產業深度分析（路徑 A 主體 / 路徑 B Step 2）
├── annual-report-analysis.md     # 年報解析（v1.3 新增，路徑 B Step 2.5）
├── company-deep-dive.md          # 公司深度分析（路徑 B Step 3）
├── decision-brief.md             # 決策簡報（可選，需 User Profile）
└── supplement-analysis.md        # 增量分析（v1.5，/supplement 觸發）
```

### 知識層（References）

**被引用者**：入口層 + 執行層
**設計目的**：避免知識雙寫與同步問題

```
references/
├── methodology/
│   ├── path-selection.md          # 路徑判斷規則（Skill 引用）
│   ├── scale-classification.md    # 規模分類標準 + 強制數據源（Skill + Agent 引用）
│   ├── quality-checklist.md       # 品質檢查清單（Skill Review 時引用）
│   ├── fetch-policy.md            # Web Fetch 黑名單與降級規則
│   ├── industry-specific-sources.md # 產業特殊資料源矩陣
│   └── annual-report-sources.md   # 各市場年報來源登記表（v1.3 新增）
├── templates/
│   ├── industry-report.md         # 產業報告模板（Agent 產出時引用）
│   ├── company-report.md          # 公司報告模板（Agent 產出時引用）
│   └── decision-brief.md          # 決策簡報模板（Agent 產出時引用）
└── cases/
    ├── _case-template.md          # Case 標準結構
    └── (案例隨使用累積，.gitignore 排除)
```

---

## 資料流：兩條分析路徑

> 詳細流程圖（含檔案調用關係）見 [`flow-diagram.md`](flow-diagram.md)。

### 路徑 A：產業 → 公司

```
使用者：「幫我研究 XX 產業」
         │
    /recon: 路徑判斷 → A
         │
    /recon: Scoping（細分領域 + 地理範圍 + 分析目的）
         │
    /recon: 交接參數 ──────────────────────────────┐
                                                   ▼
                                    Agent: 載入 industry-analysis.md
                                              │
                                    Agent: 搜尋迴圈（≤20 search + 10 fetch）
                                              │
                                    Agent: 產出產業報告
                                              │
    /recon: 呈現產業報告 ◀─────────────────────────┘
         │
    /recon: 「要深入某家公司嗎？」
         │
         ├─ 否 → Decision Brief（若 profile 存在）→ 流程結束
         └─ 是 → 進入路徑 B（從 Step 1 開始）
```

### 路徑 B：公司 → 產業

```
使用者：「幫我研究 XX 公司」
         │
    /recon: 路徑判斷 → B → Scoping → 規模預判
         │
    /recon: 交接參數 ──────────────────────────────┐
                                                   ▼
                              ┌─── Agent: Step 1 ─────────────────┐
                              │    載入 entity-verification.md     │
                              │    法律實體驗證 + 規模分類確認      │
                              └─────────────┬─────────────────────┘
                                            │
    /recon: 確認基本輪廓 ◀───────────────────┘
         │
    /recon: ★ 預分析評估（Step 4.0.5）              ← v1.3 新增
         │  資源預估 + 模型建議 + 年報計畫
         │  → 使用者確認後繼續
         │
         ▼
                              ┌─── Agent: Step 1.5 ───────────────┐
                              │    載入 stakeholder-investigation.md│
                              │    三層深度調查                     │
                              └─────────────┬─────────────────────┘
                                            │
    /recon: 確認調查結果 ◀───────────────────┘
         │
         ▼
                              ┌─── Agent: Step 2 ─────────────────┐
                              │    載入 industry-analysis.md        │
                              │    以目標公司為錨點的產業分析        │
                              └─────────────┬─────────────────────┘
                                            │
                              ┌─── Agent: Step 2.5 ────────────────┐
                              │    載入 annual-report-analysis.md    │  ← v1.3 新增
                              │    年報解析（大型=強制/中型=建議）     │
                              │    產出：數據摘要 + 衝突清單          │
                              └─────────────┬─────────────────────┘
                                            │
                              ┌─── Agent: Step 3 ─────────────────┐
                              │    載入 company-deep-dive.md        │
                              │    整合前序 + 年報數據               │
                              └─────────────┬─────────────────────┘
                                            │
    /recon: 品質 Review ◀────────────────────┘
         │
         ▼
                              ┌─── Agent: Decision Brief ─────────┐
                              │    載入 decision-brief.md            │
                              │    角色化決策簡報（零搜尋預算）       │
                              │    ※ 僅當 user-profile.md 存在      │
                              └─────────────┬─────────────────────┘
                                            │
         ▼
    cases/{company}/company-report.md（含 Version History v1.0）
    cases/{company}/decision-brief.md（若有）
    cases/{company}/case-log.md
    ★ 後續有新資料 → /supplement {company} → cases/{company}/supplements/
```

---

## 搜尋迴圈與終止機制

Agent 每個研究階段內部都運行同一套迴圈邏輯：

```
ENTER 階段
  │
  ├─ 載入對應 prompt
  │
  ▼
  WHILE 產出未達完成標準:
  │
  ├─ 執行搜尋（web_search / web_fetch）
  ├─ 評估已蒐集資訊是否足夠
  │
  ├─ IF 足夠 → 產出結構化結果 → EXIT 迴圈
  ├─ IF 不足 → 識別缺口 → 調整搜尋策略 → 繼續
  └─ IF 達搜尋上限 → 降級產出 → EXIT 迴圈
```

**搜尋上限（防止無限展開）**：

| 階段 | web_search | web_fetch | 附加限制 |
|------|------------|-----------|---------|
| 每個研究階段 | 20 次 | 10 次 | — |
| 年報解析 | 5 次 | 3 次 | 精準取得一份高密度文件 |
| 利害關係人調查（每位人物） | 5 次 | — | — |
| 關聯實體追蹤 | — | — | 最多展開 2 層 |

**核心原則**（v1.3 強化）：

- **絕對誠實**：找不到的數據標記 `[資料缺失]`，不以看似合理的猜測填補
- **數據源優先序**：年報/財報 > 官方 IR 網站 > 權威財經平台 > 新聞報導 > 搜尋 snippet

**四級證據標記**：

| 等級 | 條件 | 標記方式 |
|------|------|---------|
| 充分證據 | 多來源交叉驗證 | 正常陳述 |
| 部分證據 | 單一來源或間接推論 | `[部分證據]` |
| 證據不足 | 搜尋未果但有合理推測 | `[推測，待驗證]` |
| 無資料 | 完全搜尋不到 | `[資料缺失]` + 已嘗試策略 |

---

## 規模自適應策略

規模分類直接影響 Agent 的分析框架選擇：

| 維度 | 微型（<50人） | 中型（50-500人） | 大型/上市 |
|------|-------------|-----------------|----------|
| **強制數據源** | 商業登記 + 求職平台 | 商業登記 + 求職平台 + 年報（如公開申報） | **商業登記 + 年報（強制）+ 財經平台** |
| 財務分析 | 現金流結構推論 | 融資輪次分析 | 完整三大報表（以年報為準） |
| 組織分析 | 跳過組織圖 | 標準框架 | 完整組織分析 |
| 利害關係人 | 關鍵人物 + 關係資本（核心） | 標準三層調查 | 完整三層 + 董事會分析 |
| 產業分析 | 簡化版五力 | 標準五力 | 完整五力 + 數據支撐 |
| 盡職調查 | 法律實體 + 關鍵人物風險 | 標準框架 | 完整 DD 框架 |

---

## 預分析評估機制（v1.3 新增）

在 entity-verification 完成後、stakeholder-investigation 開始前，Skill 層向使用者呈現：

1. **資料豐富度評估**：基於上市狀態、市場、產業判斷 高/中/低
2. **年報計畫**：強制（大型/上市）/ 建議（中型公開發行）/ 不適用（微型）
3. **搜尋預算預估**：基於規模和複雜度因子估算 search/fetch 次數
4. **模型建議**：基於規模、年報需求、context 長度需求推薦最適模型
5. **時間預估**：基於歷史案例校準

使用者確認後才繼續。此步驟不消耗搜尋預算。

---

## 年報解析機制（v1.3 新增）

### 適用條件

| 規模 | 執行要求 |
|------|---------|
| 大型/上市 | **強制** |
| 中型（公開申報） | 建議 |
| 微型 | 跳過 |

### 執行位置

路徑 B Step 2.5：產業分析之後、公司深度分析之前。

### 產出

1. **年報數據摘要**（12 項數據點：營收拆分、供應商集中度、股東名單、重大合約等）
2. **衝突清單**（年報 vs 先前搜尋結果的差異，強制校正）

### 降級機制

大型/上市公司未取得年報 → company-deep-dive 的 6 個維度自動降級標註（營收拆分、供應商集中度、關係人交易、重大合約、員工趨勢、股東控制比例）。

### 來源登記

見 `references/methodology/annual-report-sources.md`，涵蓋台灣（MOPS/IR）、美國（EDGAR）、日本（EDINET）、韓國（DART）、香港（HKEXnews）、中國（巨潮）。

---

## 案例學習機制

每次完成分析後，沉澱一個 case 到 `cases/{目標名稱}/case-log.md`。

```
case 結構：
├── 分析摘要（目標、路徑、結果）
├── 踩過的坑（現象 → 根因 → 修正 → 教訓）
├── 有效搜尋策略
├── 無效搜尋策略
├── 預分析評估回顧（v1.3 新增：預估 vs 實際對照）
├── 規模適配反思
├── 品質自評
└── OSINT 天花板
```

Agent 在執行前會讀取相關 case，避免重蹈覆轍。案例會隨使用逐步累積。

---

## `.claude/` 配置層

```
.claude/
├── settings.json          # 權限配置（自動允許研究工具）
├── skills/                # 自定義指令
│   ├── recon/SKILL.md     # /recon — 統一入口，完整流程（含預分析評估）
│   ├── industry/SKILL.md  # /industry — 路徑 A 快捷入口
│   ├── company/SKILL.md   # /company — 路徑 B 快捷入口
│   └── supplement/SKILL.md # /supplement — 增量更新（v1.5 新增）
├── rules/                 # 自動載入的品質規則
│   └── output-quality.md  # 報告品質標準（檔名、必要元素、語言規範）
└── user-profile.md        # 使用者 Profile（首次使用時建立，.gitignore 排除）
```

### 設計決策

| 決策 | 選擇 | 原因 |
|------|------|------|
| 四個 skill | `/recon`（完整）、`/industry`（A）、`/company`（B）、`/supplement`（增量） | 讓進階使用者跳過路徑判斷，直接啟動；supplement 獨立成 skill 因為它不跑全流程 |
| Rules 只管輸出品質 | 研究執行規則留在 `AGENT-CORE.md` | 避免雙來源，AGENT-CORE.md 是執行規格的唯一權威 |
| 權限預設允許 | WebSearch、WebFetch 等研究工具自動允許 | 研究流程需要大量搜尋，每次都問權限會中斷節奏 |
| 預分析評估放 Skill 層 | 非 Agent 階段，零搜尋預算 | 這是流程控制決策，不是研究執行 |
| 年報降級而非阻斷 | 允許無年報繼續，但降級標註 | 使用者可能有正當理由跳過，不應阻斷流程 |
| 年報放 Step 2.5 | 產業分析之後、公司深度之前 | company-deep-dive 最需要年報數據，且作為即時 context 銜接 |

---

## 已知限制與待改善項目

### 已知限制

1. **Skill/Agent 交接依賴人工**：目前沒有自動化的參數格式驗證。
2. ~~**Output 無索引**：報告累積後缺乏搜尋與管理機制。~~ → v1.5 已解決：`cases/` 統一目錄，`ls cases/` 即可索引。
3. **預分析評估的校準基數小**：僅 2 個案例（個人理財 SaaS A/上市遊戲營運商 C），預估精度會隨案例累積改善。
4. **搜尋工具依賴**：研究品質高度依賴 web_search 和 web_fetch 的可用性與回傳品質。
5. **年報 PDF 解析依賴工具鏈**：需要 pymupdf 或 poppler 才能讀取 PDF，部分環境可能未安裝。

### 可能的改善方向

- 加入 `output/INDEX.md` 自動索引機制
- 為 Skill → Agent 的參數交接定義 schema 驗證
- 累積更多 case 以強化預分析評估的校準精度
- 探索 sub-agent 架構（Haiku 搜尋 + Opus/Sonnet 整合）降低成本
