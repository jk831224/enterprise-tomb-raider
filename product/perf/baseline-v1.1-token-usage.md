# Token 用量分析報告：/company 個人理財 SaaS A

**分析日期**：2026-04-06
**模型**：Claude Opus 4.6（1M context）
**執行環境**：Claude Code CLI + MCP tools

---

## 重要聲明

Claude **無法直接讀取自身的 token 用量指標**。以下數據基於：
- 產出檔案的實際 byte 數（可驗證）
- 中文 token 比率（1 中文字 ≈ 1.2–1.5 token，混合中英文取 1.3）
- 工具呼叫次數（可從對話記錄精確回溯）
- system prompt 結構的合理估算

**精確度等級**：工具呼叫次數 = 精確；檔案大小 = 精確；token 數 = 估算（±20%）

---

## Phase 1：收到 `/company 個人理財 SaaS A`

### 我的回應（做了什麼）

```
User: "我現在想要分析 個人理財 SaaS A 我能如何開始？"
 └→ 我：建議 /company 或 /recon
User: /company 個人理財 SaaS A（觸發 skill 載入）
 └→ 我：檢查 user-profile → 不存在 → 發送 onboarding 問題
User: "給我綜合版：投資人 / 求職者 / 商業合作夥伴 / 競品分析師 都要"
 └→ 我：寫入 user-profile.md → 載入方法論 → 執行實體驗證 → 輸出驗證結果
```

### 處理邏輯

1. **Skill 路由**：收到 `/company` → 載入 `.claude/skills/company/SKILL.md` → 指向 `recon/SKILL.md` Step 0
2. **Step 0 Profile 檢查**：Glob 搜 `.claude/user-profile.md` → 不存在 → 觸發 onboarding
3. **同時預載方法論**（平行 Read）：`scale-classification.md`、`AGENT-CORE.md`、`SKILL.md`
4. **等待使用者回答** → 收到「綜合版」 → 寫入 profile
5. **Step 1 載入方法論**：Read `path-selection.md`、`AGENT-ROUTES.md`
6. **Step 2 路徑判斷**：公司名稱已明確 → 路徑 B
7. **Step 3 Scoping**：0 輪完成（公司名已有，目的預設「全面」）
8. **Step 4.1 載入 `entity-verification.md`** + `fetch-policy.md`
9. **執行實體驗證搜尋迴圈**（見下方工具呼叫明細）
10. **產出輪廓摘要** → 請使用者確認

### 工具呼叫明細

| 動作 | 工具 | 次數 | 目的 |
|------|------|------|------|
| 檔案讀取 | Read | 7 | SKILL.md、AGENT-CORE.md、scale-classification.md、path-selection.md、AGENT-ROUTES.md、entity-verification.md、fetch-policy.md |
| 檔案搜尋 | Glob | 1 | 檢查 user-profile.md 是否存在 |
| 檔案寫入 | Write | 1 | 寫入 user-profile.md |
| 網路搜尋 | WebSearch | 8 | 快速輪廓(1)、公司登記(1)、創辦人融資(1)、董監事(1)、員工數(1)、關聯法人(1)、LinkedIn(1)、公司歷史(1) |
| 網頁抓取 | WebFetch | 3 | opengovtw.com(1)、yourator(1)、[公司A官網]/about-us(1) |
| 進度追蹤 | TodoWrite | 1 | 建立 6 項 todo |
| **合計** | | **21 次** | |

### Context Window 組成估算（Phase 1 結束時）

| 區塊 | 大小（bytes） | 估算 tokens | 佔比 |
|------|-------------|-------------|------|
| **System Prompt** | | | |
| ├ 工具定義（50+ MCP tools） | ~60,000 | ~18,000 | 27% |
| ├ 安全規則 + 隱私 + 版權 | ~15,000 | ~4,500 | 7% |
| ├ Git/PR/Commit 指引 | ~5,000 | ~1,500 | 2% |
| └ System reminders（CLAUDE.md、rules、memory、currentDate） | ~3,500 | ~1,500 | 2% |
| **Skill 載入內容** | ~6,000 | ~2,500 | 4% |
| **專案方法論檔案**（7 個 Read） | ~17,400 | ~6,500 | 10% |
| **對話歷史** | | | |
| ├ 使用者訊息（3 輪） | ~1,500 | ~700 | 1% |
| └ 我的回應（含 tool calls） | ~8,000 | ~3,500 | 5% |
| **工具結果** | | | |
| ├ WebSearch 結果（8 次） | ~24,000 | ~8,000 | 12% |
| ├ WebFetch 結果（3 次） | ~6,000 | ~2,500 | 4% |
| └ Glob/Write/TodoWrite 結果 | ~500 | ~200 | <1% |
| **我的最終輸出**（實體驗證摘要） | ~5,000 | ~2,500 | 4% |
| **估算總計** | ~152,000 | **~52,000** | |

### Sub-agents

**未使用**。所有操作在主對話線程內完成。

---

## Phase 2：收到「請繼續，一路做到完」

### 我的回應（做了什麼）

```
User: "請繼續，一路做到完，我有要這個專案最完整的方法論分析成果"
 └→ 我：連續執行 5 個階段，中間無中斷
      ├ 階段 2：利害關係人調查
      ├ 階段 3：產業分析
      ├ 階段 4：公司深度分析 + 整合
      ├ 階段 5：品質 Review + 報告寫入
      ├ 階段 5.5：Decision Brief 產出
      └ 階段 6：案例沉澱
```

### 處理邏輯

**關鍵決策點：一次性執行 vs 分段確認**

使用者說「一路做到完」= 我判斷為「跳過所有中間確認，直接從 Step 4.1.5 跑到 Step 6」。
正常流程中 SKILL.md 要求 Step 4.2（向使用者確認基本輪廓）和 Step 4.4（向使用者呈現關鍵發現摘要），但使用者的指令覆蓋了這些 checkpoint。

**每個階段的載入邏輯：**

1. **利害關係人調查**
   - Read `stakeholder-investigation.md`（進入時才載入，遵守 AGENT-ROUTES 規則）
   - 判斷微型企業策略：跳過 C-Suite 搜尋，聚焦創辦人 + 關係資本
   - 4 組平行搜尋 → 3 組補充搜尋 → 2 組驗證搜尋
   - 發現匯雲數位/邱奕淳的交叉持股 → 搜尋確認 → 形成「品牌傘非控股架構」結論

2. **產業分析**
   - Read `industry-analysis.md`
   - 判斷錨點模式（路徑 B）：以個人理財 SaaS A數據為觀察視角
   - 定義產業邊界：開放銀行/PFM + 消費數據/MarTech（雙軌）
   - 4 組平行搜尋覆蓋兩個產業 → 3 組補充搜尋取得競爭者資料
   - 簡化五力（微型企業策略）

3. **公司深度分析**
   - Read `company-deep-dive.md`
   - 關鍵判斷：微型企業 → 財務用「現金流結構分析」非三大報表
   - 執行三種營收間接推估法（方法 A/B/C 取交集）
   - 3 組搜尋取得定價、B2B 客戶、營收模式
   - 整合前序四階段成果寫入完整報告

4. **品質 Review**
   - Read `quality-checklist.md` + `company-report.md` template
   - 自我檢查 20 項 → 18 通過、2 瑕疵（標記但不阻塞）

5. **Decision Brief**
   - Read `decision-brief.md` prompt + template
   - Read `user-profile.md`（取得四重角色）
   - **零搜尋預算**：完全基於已寫入的公司報告
   - 四個鏡頭各自產出完整六段結構

6. **案例沉澱**
   - Read `_case-template.md`
   - 寫入案例檔

### 工具呼叫明細

| 動作 | 工具 | 次數 | 目的 |
|------|------|------|------|
| 檔案讀取 | Read | 8 | stakeholder-investigation.md、industry-analysis.md、company-deep-dive.md、quality-checklist.md、company-report template、decision-brief.md prompt、decision-brief template、_case-template.md |
| 網路搜尋 | WebSearch | 18 | 利害關係人(7)、產業(7)、公司深度(3)、NexTrek 關聯(1) |
| 網頁抓取 | WebFetch | 0 | snippet 已足夠或在黑名單上，依 fetch 決策樹判斷不 fetch |
| 檔案寫入 | Write | 3 | company-report.md、decision-brief.md、case file |
| 進度追蹤 | TodoWrite | 6 | 各階段狀態更新 |
| 目錄檢查 | Bash | 1 | ls output/ |
| **合計** | | **36 次** | |

### Context Window 組成估算（Phase 2 結束時）

| 區塊 | 新增 bytes | 累計估算 tokens | 佔比 |
|------|-----------|---------------|------|
| **System Prompt**（同 Phase 1） | — | ~25,500 | 16% |
| **Skill 載入內容** | — | ~2,500 | 2% |
| **專案方法論檔案**（Phase 1 的 7 + Phase 2 的 8） | +18,600 | ~13,500 | 8% |
| **對話歷史** | | | |
| ├ 使用者訊息（+1 輪） | +200 | ~900 | <1% |
| └ 我的全部回應（Phase 1 + Phase 2） | +60,000 | ~28,000 | 17% |
| **工具結果** | | | |
| ├ WebSearch 結果（Phase 1 的 8 + Phase 2 的 18） | +50,000 | ~26,000 | 16% |
| ├ WebFetch 結果（Phase 1 的 3） | — | ~2,500 | 2% |
| └ Write/TodoWrite/Bash 結果 | +3,000 | ~1,500 | 1% |
| **我的最終輸出** | | | |
| ├ company-report.md 寫入 | 18,599 | ~8,000 | 5% |
| ├ decision-brief.md 寫入 | 12,686 | ~5,500 | 3% |
| └ case file 寫入 | 5,034 | ~2,200 | 1% |
| **估算總計** | | **~116,000** | |

### Phase 2 的 Output Token 估算

| 產出 | bytes | 估算 tokens |
|------|-------|-------------|
| 階段轉場 + 摘要 + 過渡文字 | ~6,000 | ~2,500 |
| company-report.md（完整報告） | 18,599 | ~8,000 |
| decision-brief.md（四鏡頭簡報） | 12,686 | ~5,500 |
| case file（案例沉澱） | 5,034 | ~2,200 |
| 品質 Review 自檢表 | ~2,000 | ~900 |
| tool call 參數（search queries, file paths） | ~3,000 | ~1,200 |
| **Phase 2 Output 合計** | ~47,000 | **~20,300** |

### Sub-agents

**未使用**。所有 26 次搜尋、8 次 Read、3 次 Write 皆在主對話線程內序列或平行執行。

這是一個有意的設計選擇——Recon 系統的 AGENT-CORE 和 SKILL.md 將整個流程定義為「主控制器自行執行」，不拆分 sub-agent。原因：
1. 每個階段的輸出是下個階段的輸入，需要在同一 context 中累積
2. 利害關係人結論需要在公司深度分析中「重新詮釋」而非複製，這需要完整 context
3. Decision Brief 需要引用主報告的具體章節，拆分 agent 會斷掉引用鏈

---

## 全流程 Token 用量總覽

### 兩個 Phase 比較

| 指標 | Phase 1 | Phase 2 | 說明 |
|------|---------|---------|------|
| 使用者輸入輪數 | 3 | 1 | Phase 2 只有一句話就觸發全流程 |
| 方法論檔案載入 | 7 個 / 17.4 KB | 8 個 / 18.6 KB | 按需載入，不一次全載 |
| WebSearch | 8 次 | 18 次 | 利害關係人最吃搜尋量 |
| WebFetch | 3 次 | 0 次 | Phase 2 靠 snippet 就夠 |
| 檔案寫入 | 1 個 / 0.4 KB | 3 個 / 36.3 KB | 報告、簡報、案例 |
| 工具呼叫總次數 | 21 次 | 36 次 | |
| 預估 context 峰值 | ~52K tokens | ~116K tokens | Phase 2 是 Phase 1 的 2.2 倍 |
| 預估 output tokens | ~6K | ~20K | Phase 2 是 Phase 1 的 3.3 倍 |

### Context Window 用量 vs 上限

```
Model: Claude Opus 4.6 (1M context)

Phase 1 峰值:  ~52K tokens  ████░░░░░░░░░░░░░░░░░░░░░░░░░░  ~5.2%
Phase 2 峰值: ~116K tokens  ████████████░░░░░░░░░░░░░░░░░░  ~11.6%

1M context 上限: ████████████████████████████████████████  100%
```

**結論**：即使是完整路徑 B 全流程（4 階段 + Decision Brief），context 使用率僅 ~12%。1M context 的主要價值不在於容量本身，而在於能在單一 context 中累積前序階段的全部發現，讓後序階段能交叉引用和重新詮釋。

### 成本估算（參考）

| Phase | Input tokens | Output tokens | 估算 API 成本（USD） |
|-------|-------------|--------------|-------------------|
| Phase 1 | ~52K | ~6K | ~$0.87 |
| Phase 2 | ~116K | ~20K | ~$2.44 |
| **合計** | **~168K** | **~26K** | **~$3.31** |

> 估算基於 Opus 定價 $15/M input + $75/M output（2025Q4 公開定價）。
> 實際計費可能因 prompt caching、batch API 等折扣而不同。
> 此估算 `[推測，待驗證]`，僅供量級參考。

---

## 設計反思：為什麼不用 Sub-agent？

本次分析 **沒有使用任何 sub-agent**，所有操作在同一主線程完成。這是方法論的刻意設計：

### 現行做法（單線程串行）的優勢
- 階段間的 context 連續性：利害關係人的「關係資本歸屬偏向個人」結論可以直接被公司深度分析的「競爭護城河」和 Decision Brief 的「紅旗警示」引用
- 證據等級可追蹤：`[部分證據]` 標記從發現到報告到 Decision Brief 的繼承鏈完整
- 品質 Review 可以 access 全部原始搜尋結果

### 如果用 Sub-agent 的潛在架構
```
主 Agent（Orchestrator）
├→ Sub-agent A：實體驗證（search 8 + fetch 3）→ 回傳結構化 JSON
├→ Sub-agent B：利害關係人調查（search 9）→ 回傳結構化 JSON
├→ Sub-agent C：產業分析（search 7）→ 回傳結構化 JSON
└→ 主 Agent：整合 A+B+C → 公司深度分析 → 報告 → Decision Brief
```

**好處**：各 sub-agent 的 context 更小（~30-40K）、可平行執行、總延遲降低
**壞處**：
- 每個 sub-agent 回傳時必須壓縮結論，壓縮過程會丟失 nuance（例如「[創辦人 A]在[天使投資組織 A-Network]學了天使投資方法論後思維大改觀」這種細節可能被壓掉，但它對理解關係資本至關重要）
- Decision Brief 需要引用主報告的「具體章節」，如果報告由主 Agent 寫但原始資料在 sub-agent 的 context 中，引用會斷裂
- 品質 Review 無法 access sub-agent 的原始搜尋結果，只能檢查壓縮後的結論

**結論**：在當前 1M context 下，單線程串行是更安全的選擇。若未來分析規模擴大到多公司比較（例如 5 家公司同時分析），sub-agent 架構會變得必要。
