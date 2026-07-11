---
name: supplement
description: >
  增量更新既有報告。使用者說「/supplement XX公司」「/supplement XX產業」
  「補充分析」「我有新資料」「更新報告」時觸發。
  讀取既有報告 + 新 drop zone 檔案 → 產出 Supplement Memo + 更新版本鏈。
argument-hint: "[公司或產業名稱]"
allowed-tools: Read Glob Grep WebSearch WebFetch Write Edit Agent
---

# Supplement — 增量更新

## 前提

使用者已完成 `/company` 或 `/industry` 分析，並在 `cases/{target}/input/` 新增了檔案。

## 執行流程

### Step 1: 定位既有報告

1. 分析目標：`$ARGUMENTS`（如果為空，問使用者要更新哪個目標）
2. Glob `cases/{target}/company-report.md` 或 `cases/{target}/industry-report.md`
3. 如果找不到 → 告訴使用者「找不到 `{target}` 的既有報告。請先執行 `/company {target}` 完成首次分析。」，結束

### Step 2: 讀取既有報告

1. Read 主報告全文
2. 提取 Metadata（分析日期、規模分類、分析目的）
3. 提取 Version History（當前版本號）
4. 提取「Drop zone 使用紀錄」（上次分析時使用的檔案清單）

### Step 3: 掃描 Drop Zone 差異

1. Glob `cases/{target}/input/**/*`
2. 比對上次分析的檔案清單，識別**新增檔案**
3. 如果沒有新增檔案 → 告訴使用者「`cases/{target}/input/` 無新增檔案。如果你已放入新資料，請確認檔案路徑是否正確。」，結束
4. 向使用者呈現新增檔案清單，確認要處理

### Step 4: 讀取新檔案

依 `references/methodology/drop-zone.md` 規則：
- `.md` / `.txt`（< 50KB）→ 直接 Read
- PDF → Read（支援分頁，先讀第 1-3 頁判斷內容）
- 圖片 → Read（多模態）
- 如有 `type: interview-notes` frontmatter → 讀取 `confidence` 欄位

### Step 5: 載入 Supplement Analysis Prompt

載入 `agent/prompts/supplement-analysis.md`，傳入：
- 既有報告全文
- 新檔案內容
- User Profile（如 `.claude/user-profile.md` 存在）
- 既有 Decision Brief（如 `cases/{target}/decision-brief.md` 存在）

### Step 6: 產出

1. Supplement Memo → `cases/{target}/supplements/{YYYY-MM-DD}_supplement-{nn}.md`
   - `{nn}` 為序號，從 `supplements/` 目錄中現有檔案推算
2. Edit 主報告 Version History，追加新行：
   ```
   | v{X.Y} | YYYY-MM-DD | `/supplement` [觸發資料摘要] | [變更摘要] |
   ```
3. 如果 User Profile 存在 → 重新產出 Decision Brief（零搜尋預算），存入 `cases/{target}/decision-brief.md`（覆寫）

### Step 7: 呈現

向使用者呈現：
1. Supplement Memo 的核心發現（3-5 句摘要）
2. 衝突項目（如有）
3. 證據等級變動（如有）
4. 對 Decision Brief 的影響（如有）
5. 提示：「繼續有新資料可再次執行 `/supplement {target}`。」

## 品質檢查

- [ ] 搜尋預算未超 5 search / 2 fetch
- [ ] 新資料中的訪談筆記依 confidence 等級正確處理
- [ ] 證據等級標記繼承自主報告，未被擅自升級
- [ ] 主報告正文未被修改（只改 Version History）
- [ ] Supplement Memo 格式符合 `references/templates/supplement-memo.md`
