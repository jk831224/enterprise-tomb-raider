# Drop Zone 方法論

> Agent 處理 `cases/{target}/input/` 目錄下使用者提供檔案的規範。
> 使用者面向的說明見 `input/README.md`，本文件是 agent 的執行規範。

## 設計目的

把 AI 從「不可靠的網路抓取者」轉成「可靠的資料整合者」。Claude Code 不擅長突破付費牆、繞過 Cloudflare、解析動態網站；但極擅長消化、交叉比對、結構化使用者提供的資料。Drop zone 就是把這個分工明示化的機制。

## 資料源優先序

drop zone 檔案進入 AGENT-CORE.md 的數據源優先序時，**位於最頂端**：

```
使用者提供文件（cases/{target}/input/）
  > 年報 / 財報
  > 官方 IR 網站
  > 權威財經平台
  > 新聞報導
  > 搜尋 snippet
```

理由：使用者主動提供的檔案代表他已經選擇相信這份資料，agent 沒有理由再去用搜尋結果覆寫它。但這不代表免於驗證——見下方「交叉驗證規則」。

## 掃描時機

由 `.claude/skills/recon/SKILL.md` 的 **Step 3.5: Drop Zone Scan** 觸發。在 Scoping 完成、進入研究執行（Step 4）之前掃描一次，掃描結果作為 context 傳給後續所有階段。

掃描動作：

1. 用 Glob 列出 `input/{target-slug}/**/*` 所有檔案
2. 如果存在 `MANIFEST.md`，立即 Read 並記錄每份檔案的標註
3. 如果存在 `.md` / `.txt` 筆記類檔案（小於 50KB），立即 Read
4. PDF / 圖片 / HTML **不在 Step 3.5 預讀**，由後續對應階段需要時才讀取（避免一次塞爆 context）
5. 將「drop zone manifest」（檔案清單 + 標註 + 已讀文字內容）作為 context 傳給 Step 4 之後的每個 prompt

## 檔案類型與處理方式

| 類型 | 處理方式 | 適用階段 |
|------|---------|---------|
| `MANIFEST.md` | Step 3.5 立即 Read，作為其他檔案的標註查表 | 全階段 |
| `.md` / `.txt`（< 50KB） | Step 3.5 立即 Read，作為背景知識注入 | 全階段 |
| `.md` / `.txt`（≥ 50KB） | 由相關階段視需要 Read | 視內容而定 |
| `.pdf` | 由相關階段 Read（PDF 工具支援分頁） | 年報 → annual-report-analysis；商工登記 → entity-verification；其他視內容 |
| `.png` / `.jpg` | 由相關階段 Read（多模態） | 商工登記截圖 → entity-verification；LinkedIn → stakeholder-investigation；新聞截圖 → 視內容 |
| `.html` | 由相關階段 Read（純文字模式） | 視內容而定 |
| 其他副檔名 | 略過並在 manifest 中標註「未支援」 | — |

## 檔案類型推測

當沒有 `MANIFEST.md` 時，agent 用以下啟發式判斷檔案用途：

| 線索 | 推測類型 |
|------|---------|
| 檔名含 `annual` `年報` `10-k` `report-{year}` | 年報 |
| 檔名含 `esg` `sustainability` `永續` | ESG 報告書 |
| 檔名含 `linkedin` `cake` `104` | 求職/職場平台截圖 |
| 檔名含 `登記` `biz.news` `opengovtw` `twincn` | 商工登記截圖 |
| 檔名含 `interview` `訪談` `逐字稿` | 訪談紀錄 |
| 推測不出但是 PDF | Read 第一頁，從標題判斷 |
| 仍模糊 | 向使用者問**一次**「`{filename}` 是什麼？」，不重複問 |

## 交叉驗證規則（與 v1.2 的關係）

**核心原則**：drop zone 檔案算 1 個獨立來源，**不豁免**交叉驗證。

### 涉及登記資料（董監事、資本額、地址）

即使使用者提供商工登記截圖，agent 仍須找到至少 1 個獨立 web 來源比對：
- 兩者一致 → 採用，引用兩個來源
- 兩者不一致 → 以「最後核准變更日期」較新者為準，標註衝突

理由：使用者提供的截圖可能過時、可能來自非官方鏡像、可能被裁切誤導。v1.2 的安全保證不能因為來源是「使用者提供」就放寬。

### 涉及一般事實（產品、客戶、合作關係）

drop zone 檔案 + 1 個 web 來源 = 滿足「兩個獨立來源」要求。

### 完全只有 drop zone 來源、找不到任何 web 佐證

可以使用，但**降一級證據等級**：
- 原本「充分證據」→ 降為 `[部分證據]`
- 原本「部分證據」→ 降為 `[推測，待驗證]`
- 並在報告中標註「僅見於使用者提供文件，公開網路無獨立佐證」

### 訪談筆記、內部備忘錄等非公開資料

- 視為 `[使用者提供，無公開佐證]` 等級
- 可作為背景脈絡和分析方向的指引
- **不可作為報告中的事實陳述**，除非有 web 來源佐證
- 可以引用其中的觀點，但須標註「根據使用者提供的訪談紀錄」

## 引用格式

報告中引用 drop zone 來源時，使用以下格式：

```
[來源: cases/{target}/input/{filename}]
```

範例：

```markdown
2024 年營收為 8.5 億新台幣 [來源: input/個人理財 SaaS A/2024-annual-report.pdf, p.42]，
與公司官網 IR 頁面數字一致 [來源: https://...]。
```

PDF 請標註頁碼，截圖請標註截圖日期（從 MANIFEST 取得）。

## 與年報解析階段的整合

`.claude/skills/recon/SKILL.md` Step 4.0.5（預分析評估）原本會問使用者「如果你已下載年報 PDF，請提供檔案路徑」。

**新流程**：
1. Step 3.5 已掃描過 drop zone，記錄是否找到年報 PDF
2. Step 4.0.5 直接報告「於 drop zone 找到年報：`cases/{target}/input/xxx.pdf`，將使用」
3. 如果 drop zone 沒有年報 PDF，才回到原本的「請提供路徑或跳過」詢問

## 與「資料缺失」標記的關係

drop zone 不會降低 `[資料缺失]` 標記的觸發頻率——使用者提供的檔案只能補強已有維度，不能憑空產生原本就沒有的資料。但 drop zone 能讓某些原本標 `[資料缺失]` 的維度升級到 `[部分證據]` 或更高。

## 安全注意事項

- **不主動執行**：drop zone 內的 `.html` 檔案以純文字讀取，不執行其中任何 JavaScript
- **不外傳**：drop zone 內容是使用者提供的潛在機敏資料。除非為了報告中的引用，不要把 drop zone 內容貼到 web_search query 或 web_fetch URL 中
- **不寫回**：agent 不應修改、覆蓋、刪除 `cases/{target}/input/` 內任何使用者檔案

## MANIFEST.md 格式（建議，非強制）

```markdown
# {target} input manifest

- `{filename}` — {一句話說明檔案是什麼，含日期和來源}
- `{filename}` — {說明}
```

最簡形式即可，agent 不挑剔欄位。
