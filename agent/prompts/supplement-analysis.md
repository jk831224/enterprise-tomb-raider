# 增量分析（Supplement Analysis）

## 階段目標

基於既有報告 + 新增 drop zone 檔案，執行增量分析。不重跑全流程，僅處理新資料帶來的差異。

## 輸入

- 既有主報告全文（含 Version History）
- 新增 drop zone 檔案內容
- User Profile（如存在）
- 既有 Decision Brief（如存在）

## 搜尋預算

**5 search + 2 fetch**。僅用於交叉驗證新資料中的事實性聲稱。不用於重新搜尋既有報告已覆蓋的主題。

## 執行邏輯

### Step 1: 識別新資料類型

讀取新檔案的 YAML frontmatter（如有）或從檔名/內容推測類型：

| type | 處理方式 |
|------|---------|
| `interview-notes` | 依 `confidence` 欄位決定證據等級（見 `references/methodology/interview-notes-schema.md`） |
| PDF / 截圖 | 依 `references/methodology/drop-zone.md` 的檔案類型處理方式 |
| 一般 `.md` / `.txt` | 自由格式，依內容判斷 |

### Step 2: 逐項比對

對新資料中的每一個**可驗證事實**，與既有報告進行逐項比對：

1. **新發現**：新資料揭示主報告未覆蓋的維度
   - 例：報告未提及薪資結構 → 獵頭提供薪資範圍
   - 動作：寫入 Supplement Memo「新發現」區塊
   - 證據等級：依資料類型和 confidence 決定

2. **衝突**：新資料與主報告結論矛盾
   - 例：報告說員工 10-50 人 → 獵頭說目前只剩 15 人
   - 動作：消耗搜尋預算做交叉驗證，寫入「衝突」區塊
   - 如果驗證後新資料正確 → 標註建議修正
   - 如果無法驗證 → 標註兩說並存

3. **證據等級變動**：新資料讓某個 `[推測]` 升為 `[部分證據]`，或反之
   - 例：報告推測某管理層已離職 → 獵頭確認她確實已離開
   - 動作：寫入「證據等級更新」區塊

### Step 3: Decision Brief 影響評估

如果既有 Decision Brief 存在，評估 Step 2 的結果對四重鏡頭判斷的影響：
- 哪些鏡頭的核心判斷需要修正？
- 紅旗警示是否有新增或降級？
- 「你該問的問題」是否有被回答或需新增？

### Step 4: 產出

1. **Supplement Memo** → `cases/{target}/supplements/{date}_supplement-{nn}.md`（使用 `references/templates/supplement-memo.md` 格式）
2. **更新主報告 Version History**：Edit 主報告，在 Version History 表格末尾追加新行
3. **可選：重新產出 Decision Brief**（零搜尋預算，完全基於主報告 + supplement memo）

## 證據規則

- 訪談筆記 = `[使用者提供，無公開佐證]` 等級（繼承 `references/methodology/drop-zone.md`）
- 訪談筆記 + web 佐證 = 可升級到 `[部分證據]`
- **不修改主報告正文**——所有增量內容只寫在 Supplement Memo
- 報告的完整性由使用者自行判斷是否需要重跑 `/company`

## 完成標準

- [ ] 新資料中所有可驗證事實已逐項比對
- [ ] 每項比對結果歸入三類之一（新發現/衝突/證據變動）
- [ ] 搜尋預算未超標（5 search / 2 fetch）
- [ ] Supplement Memo 格式正確
- [ ] 主報告 Version History 已更新
- [ ] 如適用，Decision Brief 影響評估已完成
