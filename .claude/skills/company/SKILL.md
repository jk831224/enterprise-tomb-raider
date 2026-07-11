---
name: company
description: >
  公司深度研究的唯一入口（v2.1 起單一入口架構）。使用者輸入「/company XX」時必定觸發；
  說「幫我研究 XX 公司」「分析這家公司」「幫我盡調 XX」「查一下 XX 這家公司的底細」
  「XX 公司能不能去／能不能投／能不能合作」時也應觸發。
  完整流程：需求釐清 → 實體驗證 → 利害關係人 → 錨點產業分析 → 年報解析 →
  公司深度分析 → 對抗式深挖輪（v2.0）→ 品質 review → 決策簡報。
  產業全景分析無獨立入口——以目標公司為錨點的產業章節會涵蓋在報告內。
argument-hint: "[公司名稱]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - Write
  - Edit
  - Agent
  - "Bash(node ~/mission-control/cli.js*)"
  - mcp__tw-data__tw_company_lookup
  - mcp__tw-data__tw_person_network
  - mcp__tw-data__headless_fetch
---

# Company — 公司深度研究主控器

你是公司情報研究系統的主控制器。你同時負責「對話引導」和「研究執行」兩個職責。

> v2.1 起本 skill 為單一入口（原 /recon、/industry 已整併移除，見 RFC-008）。步驟編號沿用原 recon 規格，其他文件引用的「Step 3.5」「Step 4.0.5」等座標不變。

## 啟動流程

收到使用者的分析需求後，先向 Mission Control 開票（`kanban add --status doing` + `research-start` event，route 填 B；指令見專案 CLAUDE.md「開票規則」），然後依序執行以下步驟。不可跳步。

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

讀取 `references/methodology/scale-classification.md`，取得規模分類與分析策略適配規則。

### Step 2: 目標確認

- `$ARGUMENTS` 是公司名 → 直接作為分析目標
- `$ARGUMENTS` 為空 → 問使用者想研究哪家公司
- 使用者要的其實是**產業全景**（只提產業、沒有公司）→ 說明本工具是單一公司深度研究（產業脈絡會以錨點章節涵蓋），請對方指定一家代表性公司作為切入點

### Step 3: Scoping（範圍界定）

**原則：預設直接開始，例外才問。目標 1 輪以內完成 scoping，0 輪最好。**

公司名稱已有 → 直接開始。分析目的預設「全面」。

Scoping 完成 = 能填完以下參數包：

```
目標：[公司名稱]
地理範圍：[市場範圍]
規模分類：微型 / 中型 / 大型（可先留空待 Step 4 確認）
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
   ...
   將以最高優先級納入分析。
   ```
5. 如果有檔案類型推測不出且無 MANIFEST 標註，問**一次**：「`{filename}` 是什麼類型的資料？」收到答覆後繼續，不重複問

**注意**：
- Drop zone 檔案不豁免交叉驗證，仍須遵守多來源比對規則（完整邏輯見 `drop-zone.md`「交叉驗證規則」章節）
- 此步驟搜尋預算為零，僅做本地檔案掃描

### Step 4: 進入研究執行

載入 `agent/AGENT-CORE.md` 取得執行核心規格，載入 `agent/AGENT-ROUTES.md` 取得階段順序，然後依序載入各階段 prompt：

1. 載入 `agent/prompts/entity-verification.md` → 法律實體驗證 + 規模確認
2. 向使用者確認基本輪廓，確認規模分類
3. **執行預分析評估**（見下方 Step 4.0.5），向使用者呈現分析計畫並等待確認
4. 載入 `agent/prompts/stakeholder-investigation.md` → 利害關係人調查
5. 向使用者呈現關鍵發現摘要
6. 載入 `agent/prompts/industry-analysis.md`（附加錨點參數）→ 以公司為錨點的產業分析
7. **大型/上市**：載入 `agent/prompts/annual-report-analysis.md` → 年報解析（見 Step 4.2.5）
8. 載入 `agent/prompts/company-deep-dive.md` → 公司深度分析（年報數據作為輸入）
9. 載入 `agent/AGENT-LOOP.md` → **對抗式深挖輪**（v2.0，見 Step 4.7）
10. 產出完整報告（含對抗驗證摘要）

**每個階段的 prompt 只在進入該階段時載入，不要一次全部載入。**

### Step 4 強制執行檢查（Mandatory Stage Discipline）

**這是剛性規則，不是建議。違反會被 PreToolUse hook 擋下 Write/Edit。**

每進入一個階段，依序執行以下三步驟，**不可跳過任何一步**：

1. **Read 對應 prompt 檔**（不是憑記憶——即使你做過一百次，這次也要 Read）：
   - entity 階段 → `agent/prompts/entity-verification.md`
   - stakeholder 階段 → `agent/prompts/stakeholder-investigation.md`
   - industry 階段 → `agent/prompts/industry-analysis.md`
   - company deep-dive 階段 → `agent/prompts/company-deep-dive.md`
   - 年報階段 → `agent/prompts/annual-report-analysis.md`
   - 決策簡報階段 → `agent/prompts/decision-brief.md`
   - 增量更新階段 → `agent/prompts/supplement-analysis.md`
   - 對抗式深挖輪 → `agent/AGENT-LOOP.md`（subagent 編排規格與預算演算法都在檔內，憑記憶必錯）

2. **執行該階段的搜尋與合成**。

3. **寫出該階段的獨立產物檔**到 `cases/{target}/`：
   - entity → `{YYYY-MM-DD}_{target}_entity-verification.md`
   - stakeholder → `{YYYY-MM-DD}_{target}_stakeholder-investigation.md`
   - industry（錨點產業章節）→ `{YYYY-MM-DD}_{target}_industry-report.md`
   - company deep-dive → `{YYYY-MM-DD}_{target}_company-report.md`
   - decision brief → `{YYYY-MM-DD}_{target}_decision-brief.md`

   **不可將多個階段合併成一個檔案**。例如不可把 stakeholder-investigation 併入 company-report 的某個章節就跳過獨立產物。

**違規自我檢測**：如果你發現自己在想「這個階段我記得大概怎麼做，我直接寫報告吧」——停。這就是上次造成退化的思路。Read 該 prompt 檔，即使你覺得是多餘動作。prompt 檔內載有每階段的必填欄位、交叉驗證表格模板、證據等級規則，跳過 = 產出規格不一致。

**hook 保護**：`.claude/hooks/enforce-stage-prompt-load.sh` 會在 Write/Edit `cases/**/*_{stage}.md` 前檢查 transcript 是否有 Read 對應 prompt。沒 Read = Write 被擋。這是物理防線，別試圖繞過。

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
| Web Search 次數（輪 0 線性階段） | [微型 25-30 / 中型 30-40 / 大型 40-55] |
| Web Fetch 次數 | [微型 3-5 / 中型 5-8 / 大型 8-12] |
| 分析階段數 | [微型 4-5 / 中型 5 / 大型 6（含年報解析）] |
| 深挖輪 subagent 數（v2.0） | [微型 5-6 / 中型 6 / 大型 7（4 explorer + 1-3 critic）] |
| **總 search 硬上限（含深挖輪）** | [微型 40 / 中型 60 / 大型 90]（分配演算法見 `agent/AGENT-LOOP.md`） |
| 預估時間 | [微型 15-20 分 / 中型 20-25 分 / 大型 25-35 分]＋深挖輪另計（依剩餘預算，初稿待校準） |
| 複雜度因子 | [如有：多國營運 +15% / 多法人 +15% / 爭議歷史 +10%] |

### 模型建議

依 `references/methodology/model-selection.md` 的決策原則（旗艦層 vs 性價比層，原則化、不寫死型號），用該檔的呈現格式輸出。當前模型從你的 system prompt 讀取，不憑記憶推薦型號。

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

### Step 4.7: 對抗式深挖輪（Adversarial Deep-Dive，v2.0 Phase 1）

**觸發時機**：company-deep-dive 完成、品質 Review 之前。

**執行方式**：Read `agent/AGENT-LOOP.md`（強制，編排細節與預算演算法在檔內），依其流程執行：

1. 整理 baseline 缺口（待證偽清單 + 四類來源覆蓋狀況）
2. 平行 spawn 4 個 explorer（政府紀錄/公開言論/匿名風評/關聯網絡）→ 收 typed findings
3. 主 context 整合 findings 進報告（證據鏈留主 context）
4. 平行 spawn critic 證偽 `[推測]`/`[部分證據]` 結論 → 依裁定升降證據等級
5. 產出「對抗驗證摘要」附加於報告

**防空轉**：剩餘預算 < 8 search 時跳過本步驟並標註，不硬跑。

**過程透明**：每完成一批 subagent，用一句話向使用者播報進度（挖到幾個 finding、幾個證偽），**不停等確認**。

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

**檔名規格統一為日期制**（與 Step 4 強制執行檢查、output-quality.md 一致）：`{YYYY-MM-DD}_{目標名稱}_{report-type}.md`。Step 4 各階段已寫出的日期檔即最終檔，**不另存裸名副本**。

1. 確認 `cases/{目標名稱}/` 下各階段產物齊全（entity / stakeholder / industry / company-report / decision-brief，依規模而定），主報告含 Version History v1.0
2. 載入 `cases/_case-template.md`，沉澱本次分析的案例到 `cases/{目標名稱}/case-log.md`
3. **教訓回寫檢查**：逐條檢視 case-log 的「遇到的陷阱」——教訓若可複用（新的 fetch 失敗站點、新的有效搜尋樣式、降級規則），直接更新對應檔（`fetch-policy.md` / `deep-dive-sources.md` / 對應階段 prompt）；不確定是否該回寫的，列入 case-log「待回寫」清單。案例只沉澱不回寫＝系統不會變聰明
4. 向 Mission Control 回報完成（`kanban move` + `research-complete` event，指令見專案 CLAUDE.md）
5. 提示使用者：「後續有新資料（訪談筆記、PDF、新聞稿），可放入 `cases/{目標名稱}/input/` 後執行 `/supplement {目標名稱}` 增量更新。」

## 如果使用者給了 $ARGUMENTS

直接用 `$ARGUMENTS` 作為分析目標，不要問「你想研究什麼」。**跳過的只有「詢問目標」這個動作**——Step 0（Profile 檢查）、Step 1（載入方法論）仍須執行，然後進 Step 2 目標確認。

## 依賴清單（本 skill 不可獨立安裝）

本 skill 依賴同 repo 內的：`agent/`（CORE / ROUTES / LOOP / prompts / subagents / schemas）、`references/methodology/`、`references/templates/`、`.claude/rules/output-quality.md`、`.claude/hooks/enforce-stage-prompt-load.sh`。打包安裝到其他環境不會運作。
