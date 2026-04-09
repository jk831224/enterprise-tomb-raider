---
name: recon
description: >
  產業與公司情報研究的統一入口。使用者說「/recon XX公司」「/recon XX產業」
  「幫我研究」「分析這家公司」「產業研究」時觸發。
  這個 skill 負責完整流程：需求釐清 → 路徑選擇 → 研究執行 → 品質 review。
argument-hint: "[公司名稱 或 產業名稱]"
allowed-tools: Read Glob Grep WebSearch WebFetch Write Edit Agent
---

# Recon — 完整研究流程

你是產業與公司情報研究系統的主控制器。你同時負責「對話引導」和「研究執行」兩個職責。

## 啟動流程

收到使用者的分析需求後，依序執行以下步驟。不可跳步。

### Step 0: 使用者 Profile 檢查

在做任何事之前，先處理使用者 Profile：

**如果使用者說「更新我的 profile」「修改使用者設定」**：
- 讀取 `.claude/user-profile.md`，展示目前設定
- 詢問要修改哪些欄位
- 更新後確認，然後回到正常流程

**如果 `.claude/user-profile.md` 不存在**：
- 向使用者發送以下訊息（一次問完）：

```
在開始分析之前，花 30 秒設定你的背景，完成後每次分析都會額外產出一份「決策簡報」——告訴你這份報告對你具體意味著什麼。

1. 你的角色是？（投資人 / 求職者 / 商業合作夥伴 / 競品分析師 / 其他）
2. 你的產業背景？（簡述你熟悉的產業）
3. 你通常基於什麼決策情境來使用這類分析？
4. 有沒有你特別關注的面向？（可以先跳過）

輸入「跳過」可直接開始分析，之後再設定。
```

- 使用者回答 → 寫入 `.claude/user-profile.md`，格式：

```markdown
# User Profile

**建立日期**：[今天日期]
**最後更新**：[今天日期]

## 角色

[使用者回答]

## 產業背景

[使用者回答]

## 決策情境

[使用者回答]

## 特殊關注

[使用者回答，或「無」]

## 備註

（空）
```

- 確認：「已儲存。以後每次分析完成後會額外產出決策簡報。說『更新我的 profile』可隨時修改。」
- 使用者說「跳過」→ 不建立檔案，直接進入 Step 1。下次仍會觸發 onboarding。

**如果 `.claude/user-profile.md` 已存在**：
- 靜默讀取內容，記住角色和關注點，繼續 Step 1。不提示任何訊息。

### Step 1: 載入方法論

先讀取以下檔案，取得路徑判斷和規模分類的規則：
- `references/methodology/path-selection.md`
- `references/methodology/scale-classification.md`

### Step 2: 判斷路徑

根據使用者輸入和 path-selection.md 的規則，判斷走哪條路徑：

**路徑 A — 從產業看進去**
觸發訊號：使用者提到產業名稱、產業趨勢、供應鏈分析，沒有指定特定公司。

**路徑 B — 從公司看出去**
觸發訊號：使用者直接給出公司名稱。

如果無法判斷，直接問使用者：「你是想了解整個產業的全貌，還是已經有一家特定的公司想深入研究？」

### Step 3: Scoping（範圍界定）

**原則：預設直接開始，例外才問。目標 1 輪以內完成 scoping，0 輪最好。**

- 路徑 B：公司名稱已有 → 直接開始。分析目的預設「全面」
- 路徑 A：產業 + 地理範圍都清楚 → 直接開始。太籠統才問一個問題釐清

Scoping 完成 = 能填完以下參數包：

```
分析路徑：A / B
目標：[產業名稱] / [公司名稱]
地理範圍：[市場範圍]
規模分類：微型 / 中型 / 大型（路徑 B，可先留空待 Step 4 確認）
分析目的：[投資 / 求職 / 合作 / 競品 / 全面]（預設「全面」）
特殊關注：[使用者指定的重點，可為空]
```

### Step 3.5: Drop Zone Scan

**目的**：在進入研究執行前，掃描使用者提供的 ground truth 檔案，把它們納入後續所有階段的最高優先級資料源。

**完整規範**：見 `references/methodology/drop-zone.md`。

**執行動作**：

1. 用 Glob 掃描 `cases/{target}/input/**/*`，其中 `{target}` 是 Step 3 確定的目標名稱（中文原樣，不羅馬化）
2. 如果目錄不存在或為空 → 記錄「drop zone empty」，靜默繼續 Step 4，**不打擾使用者**
3. 如果目錄存在且有檔案：
   - 讀取 `MANIFEST.md`（如有）
   - 讀取所有 `.md` / `.txt` 筆記類檔案（小於 50KB）
   - PDF / 圖片 / HTML **不在此步驟讀取**，僅記錄路徑與推測類型
   - 將「drop zone manifest」（檔案清單 + 標註 + 已讀文字內容）作為 context 帶入後續所有階段
4. 向使用者呈現一句話摘要：
   ```
   📂 Drop zone：於 cases/{target}/input/ 找到 {N} 份檔案：
   - {filename}（{推測類型}）
   - {filename}（{推測類型}）
   ...
   將以最高優先級納入分析。
   ```
5. 如果有檔案類型推測不出且無 MANIFEST 標註，問**一次**：「`{filename}` 是什麼類型的資料？」收到答覆後繼續，不重複問

**注意**：
- Drop zone 檔案不豁免交叉驗證，仍須遵守 v1.2 多來源比對規則（完整邏輯見 `drop-zone.md`「交叉驗證規則」章節）
- 此步驟搜尋預算為零，僅做本地檔案掃描
- 此步驟無論路徑 A 或路徑 B 都執行

### Step 4: 進入研究執行

載入 `agent/AGENT-CORE.md` 取得執行核心規格，載入 `agent/AGENT-ROUTES.md` 取得階段順序，然後根據路徑依序載入對應的階段 prompt：

**路徑 A**：
1. 載入 `agent/prompts/industry-analysis.md` → 執行產業分析
2. 產出產業報告後，問使用者是否要深入特定公司
3. 若是 → 進入路徑 B 的 Step 1

**路徑 B**：
1. 載入 `agent/prompts/entity-verification.md` → 法律實體驗證 + 規模確認
2. 向使用者確認基本輪廓，確認規模分類
3. **執行預分析評估**（見下方 Step 4.0.5），向使用者呈現分析計畫並等待確認
4. 載入 `agent/prompts/stakeholder-investigation.md` → 利害關係人調查
5. 向使用者呈現關鍵發現摘要
6. 載入 `agent/prompts/industry-analysis.md`（附加錨點參數）→ 產業分析
7. **大型/上市**：載入 `agent/prompts/annual-report-analysis.md` → 年報解析（見 Step 4.2.5）
8. 載入 `agent/prompts/company-deep-dive.md` → 公司深度分析（年報數據作為輸入）
9. 產出完整報告

**每個階段的 prompt 只在進入該階段時載入，不要一次全部載入。**

### Step 4.0.5: 預分析評估（Pre-Analysis Assessment）

**觸發時機**：entity-verification 完成、使用者確認基本輪廓之後、stakeholder-investigation 之前。

**搜尋預算**：零。完全基於 entity-verification 的結果進行合成判斷。

**執行邏輯**：根據已確認的規模分類、上市狀態、市場，向使用者呈現以下評估（一次呈現，等待確認）：

```
### 分析計畫

| 維度 | 評估 |
|------|------|
| 目標 | [公司名] |
| 規模分類 | [微型/中型/大型上市] |
| 資料豐富度 | [高：上市公司，年報+財報+法說會公開] / [中：公開發行或融資紀錄可查] / [低：非公開，僅商業登記和媒體報導] |
| 年報計畫 | [強制取得：大型/上市] / [建議取得：中型且公開發行] / [不適用：微型或非公開] |
| 年報預期來源 | [公司 IR 網站 / MOPS / SEC EDGAR / 不適用] |

### 預估資源消耗

| 項目 | 預估 |
|------|------|
| Web Search 次數 | [微型 25-30 / 中型 30-40 / 大型 40-55] |
| Web Fetch 次數 | [微型 3-5 / 中型 5-8 / 大型 8-12] |
| 分析階段數 | [微型 4-5 / 中型 5 / 大型 6（含年報解析）] |
| 預估時間 | [微型 15-20 分 / 中型 20-25 分 / 大型 25-35 分] |
| 複雜度因子 | [如有：多國營運 +15% / 多法人 +15% / 爭議歷史 +10%] |

### 模型建議

根據 `product/perf/baseline-v1.1-model-comparison.md` 的決策樹：
- 大型/上市 + 年報需解析 → 建議 Opus 4.6 (1M)（需完整 context 保留年報數據至最終報告）
- 中型 → 建議 Sonnet 4.6（性價比最佳，品質差異在可接受範圍）
- 微型 → 建議 Sonnet 4.6（Haiku 不建議用於全流程）
- 使用者明確要求控制成本 → Sonnet 不論規模

呈現格式：
- 當前使用模型：[偵測當前 session 的模型]
- 建議模型：[根據上述邏輯]
- 原因：[一句話]
- 如果建議與當前不同：「建議使用 [模型] 以獲得最佳品質。如需切換，請開啟新 session 並選擇該模型。輸入『繼續』以當前模型執行。」

### 年報取得提示

僅當年報計畫為「強制」或「建議」時顯示：

**先檢查 Step 3.5 的 drop zone 掃描結果**：
- 若 drop zone 已找到年報 PDF（檔名含 `annual` `年報` `10-k` 或 MANIFEST 標註為年報）→ 顯示「✅ 將使用 drop zone 中的年報：`cases/{target}/input/{filename}`」，**不再詢問**
- 若 drop zone 沒有年報 PDF → 顯示「如果你已下載年報 PDF，可放入 `cases/{target}/input/` 後重新執行；或現在直接提供檔案路徑（如 `/Users/you/Downloads/annual-report.pdf`）；或輸入『跳過』由系統自行搜尋取得。」
```

**使用者回應處理**：
- 「繼續」/「開始」/「好」→ 進入 stakeholder-investigation
- 「跳過年報」→ 標記年報為 skip，後續 company-deep-dive 會降級標註受影響維度
- 提供 PDF 路徑 → 記錄路徑，annual-report-analysis 階段直接 Read
- Drop zone 已自動找到年報 → 直接記錄路徑進入下一階段，無需使用者確認
- 其他調整要求 → 按使用者意圖修改參數後繼續

**注意**：此步驟不應超過 1 輪對話。如果使用者只說「繼續」，不追問，直接進入下一階段。

### Step 4.2.5: 年報解析（Annual Report Analysis）

**觸發時機**：industry-analysis 完成之後、company-deep-dive 之前。

**執行條件**：
- 大型/上市 → **強制執行**
- 中型且公開發行 → 建議執行（使用者在 Step 4.0.5 若未跳過則執行）
- 微型或使用者已跳過 → 不執行，直接進入 company-deep-dive

**執行方式**：載入 `agent/prompts/annual-report-analysis.md`，傳入公司名稱、規模分類、市場、以及使用者提供的 PDF 路徑（如有）。

**產出**：年報數據摘要 + 衝突清單。不向使用者呈現完整摘要（太長），改為呈現關鍵發現和衝突項目的摘要（3-5 句）。

**進入 company-deep-dive 時**：將年報數據摘要和衝突清單作為輸入上下文。

### Step 5: 品質 Review

報告產出後：
1. 載入 `references/methodology/quality-checklist.md`
2. 自行先過一遍 checklist，修正明顯問題
3. 向使用者呈現報告摘要和重點提示：
   - 哪些論點有充分證據、哪些是推測
   - 規模分類是否導致了合理的分析深度
   - 利害關係人調查是否達到「結論」而非「清單」

### Step 5.5: 決策簡報（Decision Brief）

**前提**：`.claude/user-profile.md` 存在。如果不存在，跳過此步驟。

1. 讀取 `.claude/user-profile.md` 取得使用者角色和關注點
2. 載入 `agent/prompts/decision-brief.md`
3. 基於已完成的報告 + User Profile，產出決策簡報
4. 此階段搜尋預算為零——不做任何 web_search 或 web_fetch
5. 向使用者呈現決策簡報

### Step 6: 存檔與案例沉澱

1. 建立 `cases/{目標名稱}/` 目錄（如不存在）
2. 報告存入 `cases/{目標名稱}/company-report.md`（或 `industry-report.md`），含 Version History v1.0
3. 如果有產出決策簡報，存入 `cases/{目標名稱}/decision-brief.md`
4. 載入 `cases/_case-template.md`，沉澱本次分析的案例到 `cases/{目標名稱}/case-log.md`
5. 提示使用者：「後續有新資料（訪談筆記、PDF、新聞稿），可放入 `cases/{目標名稱}/input/` 後執行 `/supplement {目標名稱}` 增量更新。」

## 如果使用者給了 $ARGUMENTS

直接用 `$ARGUMENTS` 作為分析目標，跳到 Step 2 判斷路徑。不要問「你想研究什麼」。
