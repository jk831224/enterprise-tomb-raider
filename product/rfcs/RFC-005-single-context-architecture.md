# RFC-005：維持單 context 架構、不導入 `.claude/agents/` subagent

| 欄位 | 內容 |
|------|------|
| **狀態** | Accepted |
| **建立日期** | 2026-04-14 |
| **最後更新** | 2026-04-14 |
| **作者** | Andrew Yen |
| **對應版本** | v1.8 |
| **CHANGELOG entry** | N/A（純架構留檔，無程式碼或 prompt 變更） |
| **PRD 章節** | [PRD § 架構](../PRD.md) |
| **相關 commit** | （待 commit 後回填） |
| **觸發來源** | 2026-04-14 對話：使用者觀察到專案無 `.claude/agents/`、無 `Agent()` 呼叫，提問是否應把產業分析切成原生 subagent |

---

## 1. Summary

本 RFC 記錄一個**不做變更**的決定：維持現行「全階段共用單一 context window、以 markdown prompt on-demand 載入」的架構，不把任何階段（特別是產業分析）切成 Claude Code 原生 subagent。

這份 RFC 的價值不在於「做了什麼」，而在於**把判斷門檻寫下來**：未來任何人（包括未來的 Andrew）想重新提出「要不要導入 subagent」，可以先對照本 RFC 的三個重評條件。若都不成立，不必重做一次同樣的分析。

## 2. Background / Problem

### 觀察到的現象

- 專案無 `.claude/agents/` 目錄
- 三個 skill（`recon`、`industry`、`company`）的 `allowed-tools` 雖列了 `Agent`，但**零次實際呼叫**
- 所有階段（實體驗證、利害關係人、產業分析、年報解析、公司深度、decision brief）都在同一個主對話 context 中執行
- 階段間的資料傳遞靠**對話記憶**，不是檔案 staging

### 觸發的提問

2026-04-14 對話中，使用者提出：這看起來像是沒用到 Claude Code 原生 subagent 機制，是不是可以把「產業分析」抽出去成 `.claude/agents/industry-analyst.md`，讓它在獨立 context window 跑 10+ 次 WebSearch，完成後只回傳 summary，以此清掉主 context 的 token 壓力？

### 現況為什麼不是遺漏

經 Explore agent 勘查（2026-04-14）：

1. **階段間有強依賴**：`agent/prompts/company-deep-dive.md:92` 明確要求「如有產業分析，已回扣產業脈絡」。公司深度報告要引用產業層級的證據（供應鏈數據、KSF、競爭者市佔等），且遵守 `output-quality.md` 的「每個關鍵論點標註資料來源（URL 或報告名稱+年份）」。這需要**原始引用**存在於主 context，不是 prose summary。
2. **預算模型鎖死**：`agent/AGENT-CORE.md:41` 的「餘額可跨階段挪用」假設單一 context 追蹤全流程的 search quota。Subagent 看不到主 agent 剩餘預算，也無法把未用完的額度交還。
3. **零 subagent 使用是一致的**：整個 repo（`.claude/`、`agent/`、`product/`）無任何 `Agent()` 呼叫。這是一致的架構選擇，不是某幾個地方忘記接上。

## 3. Goals / Non-goals

### Goals

- 記錄「維持現狀」這個決定，避免未來重覆花時間重做同樣的權衡分析
- 提供**可操作的三個重評條件**，讓未來狀況變化時能快速判斷是否該重開這個議題
- 講清楚 subagent 若真要導入，**最低需要做到什麼**（結構化 findings 檔 + 預算契約），讓未來實作時不從零起跳

### Non-goals

- 不重新設計 skill / prompt loader 機制
- 不改寫 `AGENT-CORE.md` 的搜尋預算章節
- 不涉入「多公司平行分析」的實作（那是另一份 RFC 的事，若真需要）
- 不改變現有任何階段的行為

## 4. Options Considered

### Option A：Subagent + summary-only return（使用者最初的提案）

以 `.claude/agents/industry-analyst.md` 定義原生 subagent。主 agent 用 `Agent(subagent_type="industry-analyst", ...)` spawn，subagent 在獨立 context 跑 8-12 次 WebSearch + 2-3 次 WebFetch，完成後只回傳一段 prose summary。

**優點**：
- 主 context 直接省 ~50-80k token（產業階段的所有搜尋結果不進主 context）
- 實作最簡單（一份 YAML frontmatter + 一句 spawn 呼叫）
- 未來若要平行分析多家公司，subagent 天然可水平擴展

**缺點**：
- **證據鏈斷裂**：subagent 的原始搜尋結果、URL、頁碼、年份、交叉驗證來源在 subagent context 關閉時消失。主 agent 手上只有 prose summary。
- 下游 `company-deep-dive` 要做「回扣產業脈絡」時，拿不到原始引用，三條路都爛：
  - 重搜一次 → 吃掉預算且可能得到不同版本數據
  - 不標引用 → 違反 `output-quality.md` 的資料源追蹤規則
  - 標 `[部分證據]` → 諷刺，subagent 其實握有充分證據只是沒傳出來
- 預算挪用機制壞掉：subagent 要預先配固定額度，失去跨階段彈性

### Option B：Subagent + 結構化 findings 檔交接

Subagent 跑完後，除了回傳 summary 給主 agent，還**寫一份結構化檔案** `cases/{target}/_intermediate/industry-findings.md`，內含每個論點的 URL、年份、原文截句、證據等級標記。下游 `company-deep-dive` 要回扣時用 `Read()` 撈回證據。

**優點**：
- 補回 Option A 的證據鏈斷裂
- 主 context 仍然比現狀乾淨（只在需要時讀回 findings 的特定段落）
- 為未來多公司平行分析鋪路

**缺點**：
- 工程成本 3-5 小時：設計 findings schema、教 subagent 寫、教主 agent 讀、寫一個 case 校正
- 預算挪用仍然壞掉（subagent 邊界隔絕預算狀態）
- 增加一份需要維護的契約檔，後續任何階段 prompt 變更都要考慮與 findings schema 的一致性
- Token 經濟學 ROI 仍差（見 § 6 計算）

### Option C：維持單 context，寫 RFC 留檔（選定）

不動任何執行路徑，只新增本 RFC 與 README 索引更新。把「為什麼單 context 是對的」「什麼情況該重評」寫清楚。

**優點**：
- 零工程成本、零回歸風險
- 證據鏈完整、預算挪用彈性保留
- 留下可操作的決策門檻，未來議題重啟時不用從零推理
- 符合「作品集專案重視正確性」的原則：報告品質優先於架構花俏

**缺點**：
- 主 context 確實累積較多中間 token（但實測 Opus 1M 下使用率僅 ~25-30%，非瓶頸）
- 未來若需要多公司平行分析時，仍要從頭設計 subagent 架構（但那時也應該要重新設計，不是現在預先做）

## 5. Decision

**選擇**：Option C — 維持單 context，寫 RFC 留檔。

**理由**：

- **證據鏈是本專案的核心價值**：`output-quality.md` 的資料源追蹤、證據等級標記、drop zone 降級規則，全部依賴原始引用留在主 context。Option A 直接破壞這層，Option B 要額外工程才能補回。
- **Token 經濟學 ROI 差**：見 § 6。純算錢回本期 100+ 個月。
- **目前沒有平行需求**：單次研究一家公司是當前唯一場景。為「想像中的平行需求」預先投入工程成本不划算。
- **架構的簡單性本身有價值**：「全部純 markdown、零 subagent」容易維護、容易解釋、新人上手門檻低。引入 subagent 就多一層 mental model。

**被犧牲的東西**：
- 主 context 偶爾會累積到 ~300k token（在 1M 限額內仍有三倍餘裕）
- 未來若要加第 7、8 個階段可能更早撞 context 上限，屆時再重評

### 關鍵決策點

- **「subagent 讓證據鏈弱化」這句話要修正**：不是 subagent **本身**弱化，是 summary-only 的交接介面弱化。Option B 證明這可以補回來，只是成本高。這個區分對未來討論重要。
- **「主 context 乾淨」不是獨立價值**：在 1M context 下，乾淨與不乾淨的差別主要是帳面美觀，不是可用性。

## 6. 效能影響

### 設計時預估

本 RFC 無任何程式碼、prompt、skill 變更。所有維度為 0。

| 維度 | 變更前 | 變更後 | Δ |
|------|--------|--------|---|
| 預載 token（系統 prompt + skill + agent） | 現況 | 現況 | 0 |
| 平均階段新增 Read 呼叫 | 0 | 0 | 0 |
| 平均階段新增 Glob 呼叫 | 0 | 0 | 0 |
| 預期搜尋次數變化 | 現況 | 現況 | 0 |
| 預期 fetch 次數變化 | 現況 | 現況 | 0 |
| 命中率預期變化 | 現況 | 現況 | 0 |
| 證據等級分布預期變化 | 現況 | 現況 | 0 |

### Token 經濟學計算（供未來重評參考）

**產業分析階段若切 subagent 可節省的主 context token**：

| 項目 | 估計 |
|------|------|
| 8-12 次 WebSearch 結果 | 24-36k tokens |
| 2-3 次 WebFetch（網頁原文） | 20-30k tokens |
| 階段 prompt 本身 | ~3k tokens |
| Model 中間推理、輸出 | 5-15k tokens |
| **小計（可省）** | **~50-80k tokens** |
| 扣除：findings 檔讀回（Option B） | +5-15k tokens |
| **淨節省** | **~35-65k tokens** |

**在 Opus 1M context 下的佔比**：3.5-6.5%，無 context 壓力。

**成本面**：Opus 1M input ~$6/M（未快取）、~$0.6/M（cached read）。後續階段會重讀這些 token 但走 cache。粗估每 case 多付 **$0.10-0.30**。每月 5-10 case → **$1-3/月**。

**工程成本**：Option B 實作 3-5 小時。回本期 > 100 個月。

### 實測結果

N/A — 無需實測。純文件變更，沒有可量測的行為差異。

## 7. 風險

| 風險 | 嚴重度 | 緩解方式 |
|------|--------|---------|
| 未來忘記這個決定、重覆爭論同樣的議題 | 中 | 本 RFC + `product/rfcs/README.md` 索引；AGENT-CORE.md 若有編輯時，可在適當段落加一句「為何單 context：見 RFC-005」 |
| 多公司平行需求突然出現時沒意識到該重評 | 中 | § 9 明列三個重評觸發條件 |
| 1M context 模型未來降級/改用 | 低 | 三個重評條件之一即為此；屆時自然會重開本議題 |
| 這份 RFC 被當成「反對 subagent」的通則 | 低 | Summary 明寫「本決定僅適用目前架構與工作量」；Option B 留著當作未來實作起點 |

## 8. Implementation Plan

### 需要新增的檔案

- `product/rfcs/RFC-005-single-context-architecture.md` — 本檔

### 需要修改的檔案

- `product/rfcs/README.md` — 索引表新增 RFC-005 一列

### 不動的檔案

- `agent/AGENT-CORE.md`、`agent/AGENT-ROUTES.md`、所有 `agent/prompts/*.md`、`.claude/skills/**` — 本 RFC 是「不做變更」的紀錄
- `product/PRD.md`、`CHANGELOG.md` — 無功能變更

## 9. Followups / Open Questions

### 三個應該重評本 RFC 的觸發條件

若未來出現**任一**條件成立，應該重開「要不要導入 subagent」的討論：

1. **平行分析需求成形**：使用者明確要求同時研究 ≥3 家公司（投資組合、多案比較）。此時時間經濟學會壓過 token 經濟學，Option B 的 parallel spawn 價值浮現。
2. **Context 上限壓力**：若降級到 200k context 的模型，或加入新階段使 Path B 單次總量 > 500k token，Option B 的 context 瘦身才有實質意義。
3. **架構展示需求**：若 portfolio 或面試場合需要展示 multi-agent orchestration 經驗，為展示價值而實作 Option B 是合理的非技術理由。

### 預留給未來的問題

- Option B 的 findings schema 該用 markdown + frontmatter 還是 YAML？（若未來真要做再決定，不在此 RFC 範圍）
- 若 subagent 真的導入，是否一併把「利害關係人調查」切出去？（同樣有 summary-vs-evidence 的權衡，需要獨立分析）
- 現行 `跨階段挪用` 預算若未來常態性難以使用，是否應該改成「每階段獨立預算」？（這是架構簡化，與 subagent 無關）

## 10. References

- `agent/AGENT-CORE.md:15`（數據源優先序，含 MCP 位階）
- `agent/AGENT-CORE.md:31-41`（搜尋預算表 + 跨階段挪用規則）
- `agent/prompts/company-deep-dive.md:92`（「回扣產業脈絡」要求）
- `agent/prompts/industry-analysis.md`（目前產業分析 prompt）
- `.claude/rules/output-quality.md`（資料源追蹤與證據等級規則）
- Claude Code Agent tool spec：「When the agent is done, it will return a single message back to you.」— 說明 subagent summary-only 交接的機制來源
- 2026-04-14 對話：使用者提問、Explore agent 勘查報告、token 經濟學計算
