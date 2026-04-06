# Enterprise Tomb Raider — 企業祖墳探勘器

一套 Context Engineering 驅動的情報研究工作流。零程式碼，純 Markdown 架構，在 Claude Code 原生環境中運行。

> **使用前請先 ⭐ Star 或 Fork**
> 這是我的個人作品集專案。如果你覺得有用，請先 Star 或 Fork 再使用，讓我知道誰在用它。
> 有任何想法、建議或使用心得，歡迎開 [Issue](../../issues) 交流。

## 這是什麼

Enterprise Tomb Raider 幫你在做投資決策、求職評估、合作判斷前，系統性地完成情報研究。你告訴它你想了解的產業或公司，它會：

1. 引導你釐清研究範圍（不會讓你問了一個太大的問題然後得到一份空洞的報告）
2. 自主執行多階段研究（搜尋、交叉驗證、關聯實體追蹤）
3. 產出結構化的繁體中文報告，每個論點標註證據等級和來源

> 你知道霸道總裁小說裡那個經典橋段嗎？「三分鐘內，我要這間公司所有的資料！」
> 這個專案大概就是在做這件事（笑）。當然，三分鐘可能不夠，但十幾分鐘跑完一輪系統性調查是真的。
>
> **認真的提醒**：這套系統基於 LLM + 公開網路資料運作，產出的報告是「結構化的情報研究起點」，不是經過正式查核的盡職調查報告。資料可能有誤差、有遺漏、有時效性問題。請把它當作你決策前的第一輪功課，不是最後一道防線。

## 專案定位：Context Engineering

**這是一個 Context Engineering 專案**——有意識地設計「什麼資訊、在什麼時機、以什麼結構進入模型的 context window」，讓 AI 在正確的階段擁有正確的能力。

不是一個 prompt、不是一段腳本、不是一個傳統程式。整個系統由 Markdown 文件構成，透過 Claude Code 的原生機制（Skills、Rules、Agent prompts）組合成一個多階段的自主研究流程。

### 核心設計理念

1. **分層而非堆疊**：入口（Skill）負責釐清需求，執行（Agent）負責自主研究，知識（References）按需載入。三層各有邊界，不互相污染 context。
2. **人機切割點明確**：需要人類判斷的（研究範圍、優先順序）留給 Skill 對話；不需要人介入的（搜尋迴圈、交叉驗證）交給 Agent 自主跑。
3. **從失敗中學習**：每次研究完畢沉澱案例，記錄搜尋策略的成敗。下次研究同類目標時，Agent 會先讀取相關案例避免重蹈覆轍。

## 快速開始

### 在 Claude Code 使用

```bash
cd enterprise-tomb-raider
claude
```

三個指令可用：

| 指令 | 用途 | 範例 |
|------|------|------|
| `/recon` | 統一入口，自動判斷路徑 | `/recon 台積電`、`/recon AI Agent 產業` |
| `/industry` | 直接進入產業分析（路徑 A） | `/industry 東南亞跨境電商物流` |
| `/company` | 直接進入公司分析（路徑 B） | `/company 鴻海` |

也可以直接用自然語言：「幫我研究台積電」，系統會自動觸發 `/recon`。


## 兩條分析路徑

### 路徑 A：產業 → 公司

適合你想了解一個產業的全貌，還沒有特定目標公司。

```
觸發：「幫我研究 XX 產業」「XX 行業分析」「供應鏈分析」

流程：Scoping → 產業分析（歷史趨勢 + 結構定位 + 頂級玩家）
      → 可選：深入特定公司
```

### 路徑 B：公司 → 產業

適合你已經有一家想了解的公司。

```
觸發：「幫我研究 XX 公司」「公司盡職調查」

流程：Scoping → 實體驗證 → 利害關係人調查 → 產業分析（以該公司為錨點）
      → 公司深度分析 → 品質 Review
```

## 產出

報告存放在 `output/`，檔名格式：`{YYYY-MM-DD}_{名稱}_{report-type}.md`

每份報告包含：
- 來源追蹤（每個關鍵論點標註 URL 或報告名稱）
- 四級證據標記（充分證據 / 部分證據 / 推測待驗證 / 資料缺失）
- 分析日期與搜尋紀錄摘要

## 專案結構

```
enterprise-tomb-raider/
├── CLAUDE.md              # Claude Code 專案指令
├── .claude/               # Claude Code 專案配置
│   ├── settings.json      # 權限（自動允許研究工具）
│   ├── skills/            # 自定義指令
│   │   ├── recon/         # /recon — 統一入口
│   │   ├── industry/      # /industry — 產業分析快捷
│   │   └── company/       # /company — 公司分析快捷
│   └── rules/             # 品質規則（自動載入）
│       └── output-quality.md
├── agent/
│   ├── AGENT-CORE.md      # 執行核心（角色、迴圈、預算、降級、錯誤處理）
│   ├── AGENT-ROUTES.md    # 路徑與階段清單
│   └── prompts/           # 各階段執行 prompt（動態載入，不一次全讀）
│       ├── entity-verification.md
│       ├── stakeholder-investigation.md
│       ├── industry-analysis.md
│       └── company-deep-dive.md
├── references/            # 共用知識層（Skill 和 Agent 都引用）
│   ├── methodology/       # 路徑選擇、規模分類、品質檢查標準
│   ├── templates/         # 報告結構模板
│   └── cases/             # 實戰案例與已知陷阱
├── docs/
│   └── architecture.md    # 系統架構文件
└── output/                # 報告產出
```

## 架構設計

**為什麼不是一個檔案？**

原始版本是單一 SKILL.md（355 行），同時處理對話引導和自主研究。實際使用中暴露兩個問題：

1. **控制流衝突**：Skill 是靜態指令注入，適合引導對話。但利害關係人調查需要 10-30 次搜尋的自主迴圈，skill 格式下 Claude 傾向用最少步驟完成，調查深度不足。
2. **維護性**：方法論、執行指令、品質標準、案例教訓全部塞在一個檔案裡，改任何一部分都要在 355 行中定位。

**切割原則**：

| 層 | 職責邊界 | 對應檔案 |
|----|---------|---------|
| 入口（Skills） | 需求釐清、路徑選擇、流程控制 | `.claude/skills/` |
| 執行（Agent） | 自主搜尋、驗證、結構化產出 | `agent/AGENT-CORE.md` + `agent/prompts/` |
| 知識（References） | 方法論、模板、案例 | `references/` |
| 品質（Rules） | 報告格式、語言規範（自動生效） | `.claude/rules/` |

完整架構文件見 [`docs/architecture.md`](docs/architecture.md)。

## 規模自適應

系統根據目標公司規模自動調整分析框架：

| | 微型（<50人） | 中型 | 大型/上市 |
|--|-------------|------|----------|
| 財務 | 現金流結構推論 | 融資輪次 | 完整三大報表 |
| 利害關係人 | 關鍵人物 + 關係資本 | 標準三層 | 完整三層 + 董事會 |
| 產業分析 | 簡化版五力 | 標準五力 | 完整五力 + 數據 |

微型非上市企業不會出現空洞的財報分析；大型上市公司不會缺少財務數據。

## 案例學習

每次分析完成後，系統會沉澱一個 case 到 `references/cases/`，記錄踩過的坑和有效的搜尋策略。Agent 執行前會讀取相關案例，避免重蹈覆轍。

案例會隨著使用逐步累積。案例模板見 `references/cases/_case-template.md`。

## 設計決策記錄

| 決策 | 選擇 | 原因 |
|------|------|------|
| Skill/Agent 切割點 | 邊界在「使用者判斷」vs「機器執行」 | Scoping 需要人類判斷，搜尋迴圈不需要 |
| Prompts 獨立成檔 | 每階段一個檔案，動態載入 | 避免 AGENT-CORE.md 重蹈 SKILL.md 的肥大問題 |
| References 獨立 | 放在 Skill 和 Agent 之外 | 兩層都要用，放共用層避免雙寫 |
| Cases 標準結構 | 統一模板 + 四種必記項目 | 讓 Agent 能從歷史中學習 |

---

## Author

**Andrew Yen（顏士傑）**

目前準待業中。近期經歷是 AdTech 領域的產品經理。

職涯從政府標案新創起步，歷經 QA 測試工程師、CRM 專案經驗，到廣告科技 PM。這條不算典型的路徑，讓我累積了跨領域的產品思維：從搞懂政府標書的眉角、建立系統邊界的概念、梳理企業部門 BPMN 流程，到在 AdTech 領域處理平台規劃、流量數據儀表板、跨部門協作的廣告格式開發 SOP。

這個專案源自一個實際痛點：在評估合作方、準備面試、判斷市場機會時，我需要快速建立對一家陌生公司的完整認知。手動搜集和交叉比對公開資訊既耗時又容易遺漏。Enterprise Tomb Raider 是我嘗試用 Context Engineering 解決這個問題的實踐——把結構化的情報蒐集交給 Agent，讓人專注在「這些資訊對我的決策意味著什麼」。

### 方法論啟發

分析方法論的靈感來自 YouTube 頻道[「商談，不廢話」](https://www.youtube.com/@RealBizChat)——用結構化的框架拆解商業情報，而非堆砌資訊。這個頻道讓我意識到：好的公司研究不是「查到越多越好」，而是「問對問題、用對框架」。

在做這個專案之前，我也嘗試過其他 AI Agent 的開發。那些經驗讓我學到一件事：Agent 的價值不在於它能搜多少資料，而在於你怎麼設計它的思考結構。這也是為什麼這個專案最終走向 Context Engineering 而非傳統的 RAG 或 workflow automation。

### 關於分享這件事

[Vincent Cheng-Wen Yu](https://www.threads.com/@vincentyucw) 在一篇 Threads 貼文中提到：[師父多半只能給你 Beta：真正的 Alpha 為何無法靠「上課」獲取？](https://www.threads.com/@vincentyucw/post/DUmRNUbE3_5)——能被系統化教學的，多半是 Beta（已知框架）；真正的 Alpha（超額洞見）來自實戰中的個人判斷。

我很清楚這個專案分享出來的東西是 Beta 等級：一套可複製的研究框架和 Context Engineering 的實踐方式。但我相信 Beta 也有價值——至少它能幫你省下從零開始摸索的時間，讓你更快到達可以累積自己 Alpha 的起點。

如果你有更好的做法、踩過類似的坑、或者單純想聊聊 Context Engineering，歡迎開 [Issue](../../issues) 或直接聯繫我。一起交流，一起做出更多有趣的東西。

- GitHub：[@jk831224](https://github.com/jk831224)
- LinkedIn：[Shih-chieh Yen](https://www.linkedin.com/in/shihchiehyen)
