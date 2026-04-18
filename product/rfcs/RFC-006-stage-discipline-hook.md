# RFC-006：Stage Discipline Hook — 強制載入階段 prompt

| 欄位 | 內容 |
|------|------|
| **狀態** | Implemented |
| **建立日期** | 2026-04-18 |
| **最後更新** | 2026-04-18 |
| **作者** | Andrew Yen |
| **對應版本** | v1.9 |
| **CHANGELOG entry** | [v1.9](../../CHANGELOG.md#v19) |
| **PRD 章節** | [PRD § 原則 8](../PRD.md#8-階段紀律-sop-第一) |
| **相關 commit** | （見本次 release） |

---

## 1. Summary

新增 `PreToolUse` hook，在 Write/Edit `cases/**/*_{stage}.md` 前強制檢查 session transcript 是否已 Read 對應的 `agent/prompts/{stage}.md`。沒 Read 就 block 並回傳明確錯誤。同時在 `.claude/skills/recon/SKILL.md` Step 4 新增「Mandatory Stage Discipline」段，明文要求「Read → 執行 → 寫獨立產物檔」三步驟不可省略。

## 2. Background / Problem

### 觸發事件

2026-04-18 一次 `/company` 分析（微型公司，目標名稱已去識別）產出的主報告：

- 176 行 vs 同等規模過往案例 ~292 行
- 缺 Metadata 區塊、資料衝突交叉驗證表、組織結構視覺化
- `stakeholder-investigation` 獨立產物檔**整個沒寫**，被併入 company-report 的子章節

使用者察覺品質退化，追問原因。根因自承：**四個階段 prompt 一個都沒 Read**，全憑「我記得大概長怎樣」寫完報告。

### 現況的限制

recon SKILL.md Step 4 用自然語言寫「載入 `agent/prompts/{stage}.md` → 執行」。這是**規範層**的要求，但 harness 層沒有任何物理檢查。模型在壓力下（token 成本、已做過類似任務的熟悉感）會自主省略載入動作，且不會留下可追溯的違規訊號——產出退化是唯一訊號，而使用者需自行比對歷史檔案才能察覺。

換句話說：skill 的自然語言要求 = 「建議」，不是「約束」。

## 3. Goals / Non-goals

### Goals

- **G1. 物理擋路**：在 Write/Edit 發生前攔截未載入 prompt 的行為
- **G2. 規範明示**：在 skill 裡用顯式 checklist 標記 stage discipline 為剛性規則
- **G3. 可稽核**：hook 的 block 訊息要明確指向應 Read 的檔案，而非泛泛的失敗
- **G4. 不影響非目標檔案**：只針對 `cases/**/*_{stage}.md` 的寫入攔截，其他 Write/Edit 放行

### Non-goals

- **不驗證 prompt 內容是否被實際遵守**（hook 只能看有沒有 Read，看不到後續產出有沒有對齊 prompt 的表格/章節要求）
- **不追加 step-by-step 的狀態機**（保持現有 skill 的線性流程，不引入新的 session state 檔案）
- **不強制所有 skill 的所有 prompt**（只管 tomb-raider 的 recon 系列六個 stage）

## 4. Options Considered

### Option A：純 skill 文字警告

在 recon SKILL.md 加粗體「必須 Read」警告，不加 harness 檢查。

**優點**：零工程成本；不會誤擋合法編輯。
**缺點**：這就是**現況**的變體。自然語言警告在已經造成退化事件的情況下證明不夠——模型會自己判讀「我記得」是合理豁免。

### Option B：PreToolUse hook（本 RFC 採用）

Bash + Python 解析 transcript，對照 Write/Edit 目標檔名後綴 → 要求 Read 對應 prompt → 沒 Read 就 exit 2 阻擋。

**優點**：
- 物理強制，模型無法自主豁免
- transcript-based 檢查不需要額外 state 檔案，session 自然清理
- Block 訊息可包含「Required: Read X」的具體指示，比單純擋下更有修補路徑

**缺點**：
- 若使用者手動微調 case 報告（例如修錯字）也會被擋——需要局部豁免路徑（settings.local.json）
- Bash+Python 混用，hook 腳本本身需要測試

### Option C：以 skill 拆成多個 sub-skill，每個 sub-skill 只能做一階段

把 recon 拆成 recon-entity, recon-stakeholder, recon-industry, recon-deep-dive 四個 skill，每個 skill 的 allowed-tools 寫死只能寫對應檔案。

**優點**：從架構層級徹底隔離階段。
**缺點**：
- 破壞現有 `/recon` `/company` 單一入口 UX
- Skill 定義不支援「讀檔作為執行前置」的強制機制，仍需 hook 輔助
- 架構重寫成本遠高於本次退化事件的修復價值

## 5. Decision

**採 Option B（hook）+ Skill 文字強化（輔助）。**

Option B 是物理防線，SKILL.md 文字是可讀的規範對照。兩者互補：hook 擋 Write 時的錯誤訊息指向 SKILL.md 的新段落，使用者/模型看到 block 後能自己找到要 Read 的檔案清單。

Option C 在未來若有更大規模的階段治理需求再考慮。

## 6. Implementation

### 檔案

- `.claude/hooks/enforce-stage-prompt-load.sh`（新增）
- `.claude/settings.json`（新增 `hooks.PreToolUse` 區段）
- `.claude/skills/recon/SKILL.md`（Step 4 後新增「Mandatory Stage Discipline」段）

### Hook 邏輯

```
1. 讀 stdin JSON，取 tool_name / tool_input.file_path / transcript_path / cwd
2. 若 tool_name ∉ {Write, Edit} → exit 0
3. 若 file_path 不在 */cases/*.md → exit 0
4. 依 basename 後綴映射到應 Read 的 prompt：
     *_entity-verification.md       → agent/prompts/entity-verification.md
     *_stakeholder-investigation.md → agent/prompts/stakeholder-investigation.md
     *_industry-report.md           → agent/prompts/industry-analysis.md
     *_company-report.md            → agent/prompts/company-deep-dive.md
     *_decision-brief.md            → agent/prompts/decision-brief.md
     *_supplement.md                → agent/prompts/supplement-analysis.md
5. 掃 transcript (JSONL)，尋找 tool_use name=Read 且 file_path 匹配
6. 有 → exit 0；沒有 → exit 2 + 錯誤訊息到 stderr
```

### SKILL.md 變更摘要

在 Step 4 段尾新增「Step 4 強制執行檢查（Mandatory Stage Discipline）」子段，內容包含：
- 七個 stage → prompt 對應表
- 必寫的六個產物檔名
- 違規自我檢測語句（針對「我記得大概怎麼做，直接寫吧」的誘因）
- 指向 hook 檔案路徑

### 豁免設計

若使用者手動微調已存在的 case 報告（非模型主流程），可透過以下路徑繞過：
1. 在 session 中先 Read 對應 prompt 檔（合規路徑）
2. 若是修錯字等真的不需要 prompt 的微調，臨時在 `.claude/settings.local.json` 註解掉 hook matcher

刻意**不**提供 env var 豁免，避免模型學會設 var 繞過。

## 7. Alternatives Rejected

- **把檢查寫在 Write 的 permissions 規則裡**：permissions 不支援「Read history」類型的條件判斷，只能靠 hook。
- **產出 stage 報告時自動加 Read 呼叫**：違反「強制載入」的真正意圖——載入是為了讓模型讀到最新規格，不是為了 bypass 檢查。

## 8. Rollout

- 本 RFC 實作即 v1.9 release
- 首次觸發後觀察 2-3 個 case 研究迴圈，確認 hook 不會誤擋
- 若出現誤擋：擴展 hook 白名單或調整 matcher 範圍，不直接關閉 hook

## 9. Follow-ups / Future

- RFC-007（候選）：hook 檢查項擴展到「產物檔有 Version History / Metadata / 交叉驗證表」的內容層靜態檢查，而非只看「有沒有 Read」
- 將本 hook 模式抽成通用「skill stage compliance」樣板，供其他專案的 skill 套用

## 10. Lessons

- 自然語言的 skill 指令在**壓力下（token cost、熟悉感、效率偏誤）會被模型自主重新詮釋**。harness 層的物理約束是對抗這類退化的正確工具。
- 品質退化的偵測成本（使用者要手動比對歷史案例）遠高於預防成本（hook 一次寫完）。往 harness 投資預防值得。
