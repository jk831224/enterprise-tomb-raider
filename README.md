# Enterprise Tomb Raider — 企業祖墳探勘器

一個 Context Engineering 的 reference implementation。用產業與公司情報研究當載體，示範如何用純 Markdown 分層設計，在 Claude Code 原生環境中組出一個多階段自主 agent，不寫一行程式。

> 2026 年的 agent 競爭不在於誰接了更多工具，而在於誰能讓 agent 在正確的階段只讀正確的資訊。這個專案是我對這句話的一個實作。

---

## Why this exists

2026 年的共識是：Agent 的成敗不在模型大小，而在 Context Engineering。什麼資訊、在什麼時機、以什麼結構進入模型的 context window。但多數人談 Context Engineering 還停在概念層，真正可讀、可跑、規模剛好的範例很少。

這個專案是我用「產業/公司情報研究」這個實際痛點，做出的一個 Context Engineering 參考實作。你可以直接拿來做研究，也可以把這套四層架構（Skills / Agent / References / Rules）以及 harness 層的 Hooks 約束機制，移植到你自己的問題上。

> 你知道霸道總裁小說裡那個經典橋段嗎？「三分鐘內，我要這間公司所有的資料！」
> 這個專案大概就是在做這件事（笑）。當然，三分鐘可能不夠，但十幾分鐘跑完一輪系統性調查是真的。

---

## 這是什麼

Enterprise Tomb Raider 幫你在做投資決策、求職評估、合作判斷前，系統性地完成情報研究。你告訴它你想了解的產業或公司，它會：

1. 引導你釐清研究範圍（不會讓你問了一個太大的問題然後得到一份空洞的報告）
2. 自主執行多階段研究（搜尋、交叉驗證、關聯實體追蹤、年報解析）
3. 產出結構化的繁體中文報告，每個論點標註證據等級和來源

**認真的提醒**：這套系統基於 LLM 與公開網路資料運作，產出的報告是結構化的情報研究起點，不是經過正式查核的盡職調查報告。資料可能有誤差、有遺漏、有時效性問題。請把它當作你決策前的第一輪功課，不是最後一道防線。

## 專案定位：Context Engineering

這個專案有意識地設計「什麼資訊、在什麼時機、以什麼結構進入模型的 context window」，讓 AI 在正確的階段擁有正確的能力。

整個系統由 Markdown 文件構成，透過 Claude Code 的原生機制（Skills、Rules、Agent prompts、Hooks）組合成一個多階段的自主研究流程，不依賴傳統程式或腳本。

### 核心設計理念

1. **分層而非堆疊**：入口（Skill）負責釐清需求，執行（Agent）負責自主研究，知識（References）按需載入。三層各有邊界，不互相污染 context。
2. **人機切割點明確**：研究範圍與優先順序這類需要人類判斷的事留給 Skill 對話；搜尋迴圈與交叉驗證這類機械工作交給 Agent 自主跑。
3. **從失敗中學習**：每次研究完畢沉澱案例，記錄搜尋策略的成敗。下次研究同類目標時，Agent 會先讀取相關案例避免重蹈覆轍。
4. **規範不夠就用約束**：關鍵 SOP 不是靠自然語言的 skill 規則哀求模型遵守，而是用 harness 層的 hook 物理擋住違規的寫入路徑（詳見下方「從規範到約束」一節）。

## 快速開始

### 在 Claude Code 使用

```
cd enterprise-tomb-raider
claude
```

Claude Code 啟動後，四個指令之間的路徑選擇是自動的，你不用記：

| 指令 | 用途 | 範例 |
| --- | --- | --- |
| `/recon` | 統一入口，自動判斷路徑 | `/recon 台積電`、`/recon AI Agent 產業` |
| `/industry` | 直接進入產業分析（路徑 A） | `/industry 東南亞跨境電商物流` |
| `/company` | 直接進入公司分析（路徑 B） | `/company 鴻海` |
| `/supplement` | 對既有報告做增量更新 | `/supplement 鴻海` |

也可以直接用自然語言：「幫我研究台積電」，系統會自動觸發 `/recon`。

> 首次使用會觸發一次 **User Profile 設定**（可跳過）。設定之後，每次分析完成會額外產出**決策簡報（Decision Brief）**，根據你的角色（投資人／求職者／合作方／競品分析師／盡職調查方）重新解讀報告重點。

## 兩條分析路徑

### 路徑 A：產業 → 公司

適合你想了解一個產業的全貌，還沒有特定目標公司。

```
觸發：「幫我研究 XX 產業」「XX 行業分析」「供應鏈分析」

流程：Scoping → 產業分析（歷史趨勢 + 結構定位 + 頂級玩家）
      → 可選：深入特定公司（進入路徑 B）
      → 可選：Decision Brief（若已設定 User Profile）
```

### 路徑 B：公司 → 產業

適合你已經有一家想了解的公司。

```
觸發：「幫我研究 XX 公司」「公司盡職調查」

流程：Scoping → 實體驗證 → 利害關係人調查
      → 產業分析（以該公司為錨點）
      → 年報解析（大型/上市強制、中型建議、微型跳過）
      → 公司深度分析 → 品質 Review
      → 可選：Decision Brief（若已設定 User Profile）
```

## 產出

報告存放在 `cases/{目標}/`，檔名格式：`{YYYY-MM-DD}_{名稱}_{report-type}.md`

每個 case 目錄會同時包含：

- 多份階段性報告（entity-verification / stakeholder-investigation / industry-report / company-report / decision-brief）
- `input/` 子目錄：drop zone。你可以把手邊的 PDF、截圖、訪談紀錄丟進來，Agent 會優先採用（但不豁免交叉驗證）
- 跑過 `/supplement` 後的 Supplement Memo 與版本鏈

每份報告包含：

- 來源追蹤（每個關鍵論點標註 URL 或報告名稱）
- 四級證據標記（充分證據 / 部分證據 / 推測待驗證 / 資料缺失）
- 分析日期與搜尋紀錄摘要

## 專案結構

```
enterprise-tomb-raider/
├── CLAUDE.md                # Claude Code 專案指令
├── .claude/                 # Claude Code 專案配置
│   ├── settings.json        # 權限 + hooks 註冊
│   ├── skills/              # 自定義指令
│   │   ├── recon/           # /recon — 統一入口
│   │   ├── industry/        # /industry — 產業分析快捷
│   │   ├── company/         # /company — 公司分析快捷
│   │   └── supplement/      # /supplement — 增量更新
│   ├── rules/               # 品質規則（自動載入）
│   │   └── output-quality.md
│   └── hooks/               # harness 層物理檢查
│       └── enforce-stage-prompt-load.sh   # 沒載入階段 prompt 就不許寫報告（RFC-006）
├── agent/
│   ├── AGENT-CORE.md        # 執行核心（角色、迴圈、預算、降級、錯誤處理）
│   ├── AGENT-ROUTES.md      # 路徑與階段清單
│   └── prompts/             # 各階段執行 prompt（按階段動態載入）
│       ├── entity-verification.md
│       ├── stakeholder-investigation.md
│       ├── industry-analysis.md
│       ├── annual-report-analysis.md
│       ├── company-deep-dive.md
│       ├── decision-brief.md
│       └── supplement-analysis.md
├── references/              # 共用知識層（Skill 和 Agent 都引用）
│   ├── methodology/         # 路徑選擇、規模分類、年報來源、drop zone 規範、品質檢查
│   ├── templates/           # 報告結構模板
│   └── cases/               # 已去識別化的案例知識庫（Agent 執行前讀取）
├── cases/                   # 你自己在本機跑出來的真實研究案例（gitignored）
├── product/                 # PM 工件層：PRD、架構文件、流程圖、RFC、效能報告
└── README.md
```

完整架構文件見 [`product/architecture.md`](./product/architecture.md)，設計決策脈絡見 [`product/rfcs/`](./product/rfcs/)。

### 兩個 `cases/` 目錄的差別

這是 fork 下來自己用時最容易搞混的一點：

| 目錄 | 內容 | Git 狀態 | 給誰讀 |
| --- | --- | --- | --- |
| `cases/` | 你本機跑出來的真實調查，含目標公司全名、人名、敏感資訊 | **gitignored**（只有 README 與範本 tracked） | 只有你自己 |
| `references/cases/` | 已去識別化的案例知識庫，記錄過往踩過的坑和有效的搜尋策略 | 公開推送 | Agent 執行前讀取、以及 fork 這份 repo 的其他人 |

意思是：**你 fork 下來自己用，你的調查結果會落在本機 `cases/`，不會自動推回公開倉庫**。你得先把它去識別化、搬進 `references/cases/`，才會變成公開知識庫的一部分。這個專案內建了一個 `/deidentify-push` skill 協助這個流程。

## 架構設計

2026 上半年常見的 agent 失敗模式之一，是把所有邏輯塞進一個大 prompt 或大 skill 檔案，結果是 context 污染、邏輯耦合、改一處要動全身。這個專案在實作過程中踩進了同一個坑，也爬出來了。以下是重構的記錄。

**為什麼不是一個檔案？**

原始版本是單一 SKILL.md（355 行），同時處理對話引導和自主研究。實際使用中暴露兩個問題：

1. **控制流衝突**：Skill 是靜態指令注入，適合引導對話。但利害關係人調查需要 10 到 30 次搜尋的自主迴圈，skill 格式下 Claude 傾向用最少步驟完成，調查深度不足。
2. **維護性**：方法論、執行指令、品質標準、案例教訓全部塞在一個檔案裡，改任何一部分都要在 355 行中定位。

**切割原則**：

| 層 | 職責邊界 | 對應檔案 |
| --- | --- | --- |
| 入口（Skills） | 需求釐清、路徑選擇、流程控制 | `.claude/skills/` |
| 執行（Agent） | 自主搜尋、驗證、結構化產出 | `agent/AGENT-CORE.md` + `agent/prompts/` |
| 知識（References） | 方法論、模板、案例 | `references/` |
| 品質（Rules） | 報告格式、語言規範（自動生效） | `.claude/rules/` |
| 約束（Hooks） | harness 層物理檢查，擋住違反 SOP 的寫入 | `.claude/hooks/` |

## 從規範到約束：Stage Discipline Hook

Context Engineering 有一個容易被忽略的失效模式：**規範層（自然語言的 Skill、Rules）在壓力下會被模型自主重新詮釋**。

這個專案實際發生過一次典型退化：一份應該產出六個獨立階段檔的公司分析，因為模型「我記得大概怎麼做」，把四個階段 prompt 一個都沒讀，全部擠進同一份主報告，最後產出缺 metadata、缺資料衝突交叉驗證表、缺組織結構視覺化——176 行，而同等規模的過往案例是 ~292 行。

問題不在模型笨，而在：**Skill 的自然語言要求 = 「建議」，不是「約束」。** 只要 token 成本與熟悉感同時存在，模型就會自主豁免規範，且退化只能透過人工比對歷史檔案才看得出來——偵測成本遠高於預防成本。

v1.9（RFC-006）的解法是把規範升級為 harness 層的物理約束。`.claude/hooks/enforce-stage-prompt-load.sh` 是一個 `PreToolUse` hook，在 Write／Edit 任何 `cases/**/*_{stage}.md` 檔案之前：

1. 讀 session transcript
2. 檢查對應階段的 `agent/prompts/{stage}.md` 是否真的被 Read 過
3. 沒 Read 就 `exit 2`，並在錯誤訊息中明確指出缺的是哪支 prompt

對 Context Engineering 來說，這個設計的意義是：**當你發現模型會繞過規範，正確的對策不是把規範寫得更嚴厲，而是讓 harness 層擋住違規的物理路徑。** 規範保留可讀性，約束保留強制力，兩者互補而不互斥。

完整設計脈絡見 [`product/rfcs/RFC-006-stage-discipline-hook.md`](./product/rfcs/RFC-006-stage-discipline-hook.md)。

## 規模自適應

多數 agent 對 SMB 和上市公司用同一套分析框架，結果兩邊都不準。這個專案對規模敏感，系統會根據目標公司規模自動調整分析框架：

|  | 微型（<50人） | 中型 | 大型/上市 |
| --- | --- | --- | --- |
| 財務 | 現金流結構推論 | 融資輪次 | 完整三大報表 |
| 利害關係人 | 關鍵人物 + 關係資本 | 標準三層 | 完整三層 + 董事會 |
| 產業分析 | 簡化版五力 | 標準五力 | 完整五力 + 數據 |
| 年報解析 | 跳過 | 建議執行 | 強制執行 |

微型非上市企業不會出現空洞的財報分析；大型上市公司不會缺少財務數據。

## 案例學習

每次分析完成後，系統會沉澱一個 case 到 `references/cases/`（去識別化後），記錄踩過的坑和有效的搜尋策略。Agent 執行前會讀取相關案例，避免重蹈覆轍。

案例會隨著使用逐步累積。案例模板見 [`references/cases/_case-template.md`](./references/cases/_case-template.md)。

## 設計決策記錄

| 決策 | 選擇 | 原因 |
| --- | --- | --- |
| Skill/Agent 切割點 | 邊界在「使用者判斷」vs「機器執行」 | Scoping 需要人類判斷，搜尋迴圈不需要 |
| Prompts 獨立成檔 | 每階段一個檔案，動態載入 | 避免 AGENT-CORE.md 重蹈 SKILL.md 的肥大問題 |
| References 獨立 | 放在 Skill 和 Agent 之外 | 兩層都要用，放共用層避免雙寫 |
| Cases 雙目錄 | 本機真實案例與公開知識庫分離 | 讓 fork 使用者在不洩漏敏感資訊的前提下也能貢獻 |
| 規範升級為約束 | 關鍵 SOP 用 PreToolUse hook 強制 | 自然語言規範會在壓力下被模型自主重新詮釋 |

---

## 使用前請先 Star 或 Fork

這是我的個人作品集專案。如果你覺得有用，請先 Star 或 Fork 再使用，讓我知道誰在用它。有任何想法、建議或使用心得，歡迎開 [Issue](https://github.com/jk831224/enterprise-tomb-raider/issues) 交流。

---

## Author

**Andrew Yen（顏士傑）**

目前準待業中。近期經歷是 AdTech 領域的產品經理。

職涯從政府標案新創起步，歷經 QA 測試工程師、CRM 專案經驗，到廣告科技 PM。這條不算典型的路徑，讓我累積了跨領域的產品思維：從搞懂政府標書的眉角、建立系統邊界的概念、梳理企業部門 BPMN 流程，到在 AdTech 領域處理平台規劃、流量數據儀表板、跨部門協作的廣告格式開發 SOP。

這個專案源自一個實際痛點：在評估合作方、準備面試、判斷市場機會時，我需要快速建立對一家陌生公司的完整認知。手動搜集和交叉比對公開資訊既耗時又容易遺漏。Enterprise Tomb Raider 是我用 Context Engineering 解決這個問題的實踐——把結構化的情報蒐集交給 Agent，讓人專注在「這些資訊對我的決策意味著什麼」。

對我來說，它也是一個自我驗證：非工程背景的 PM，在 2026 年的 agentic tooling 下能走多遠。

### 方法論啟發

分析方法論的靈感來自 YouTube 頻道[「商談，不廢話」](https://www.youtube.com/@RealBizChat)。它讓我意識到：好的公司研究不是「查到越多越好」，而是「問對問題、用對框架」。

在做這個專案之前，我也嘗試過其他 AI Agent 的開發。那些經驗讓我學到一件事：Agent 的價值不在於它能搜多少資料，而在於你怎麼設計它的思考結構。這也是為什麼這個專案最終走向 Context Engineering，而不是傳統的 RAG 或 workflow automation。

### 關於分享這件事

[Vincent Cheng-Wen Yu](https://www.threads.com/@vincentyucw) 在一篇 Threads 貼文中提到[師父多半只能給你 Beta：真正的 Alpha 為何無法靠「上課」獲取？](https://www.threads.com/@vincentyucw/post/DUmRNUbE3_5)——能被系統化教學的，多半是 Beta（已知框架）；真正的 Alpha（超額洞見）來自實戰中的個人判斷。

我很清楚這個專案分享出來的東西是 Beta 等級：一套可複製的研究框架和 Context Engineering 的實踐方式。但 Beta 也有價值。它能幫你省下從零開始摸索的時間，讓你更快到達可以累積自己 Alpha 的起點。

如果你有更好的做法、踩過類似的坑、或者單純想聊聊 Context Engineering，歡迎開 [Issue](https://github.com/jk831224/enterprise-tomb-raider/issues) 或直接聯繫我。

- GitHub：[@jk831224](https://github.com/jk831224)
- LinkedIn：[Shih-chieh Yen](https://www.linkedin.com/in/shihchiehyen)
