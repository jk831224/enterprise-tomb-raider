# Cases — 分析案例統一目錄

每個分析目標（公司或產業）一個資料夾。進入任一資料夾即可看到全貌：使用者提供的資料 + 報告 + 增量更新 + 學習紀錄。

## 目錄結構

```
cases/
├── {公司或產業名稱}/
│   ├── input/                  # Drop Zone（使用者餵資）
│   │   ├── MANIFEST.md         # （選用）檔案標註
│   │   ├── xxx-annual-report.pdf
│   │   └── headhunter-notes.md
│   ├── company-report.md       # 主報告（含 Version History）
│   ├── decision-brief.md       # 決策簡報
│   ├── supplements/            # 增量更新 memos
│   │   └── 2026-04-10_supplement-01.md
│   └── case-log.md             # 陷阱紀錄 + 案例沉澱
```

## 怎麼用

### 首次分析

執行 `/company XX公司` 或 `/recon XX公司`，系統會自動：
1. 建立 `cases/XX公司/` 資料夾
2. 掃描 `cases/XX公司/input/`（如有預先放入的檔案）
3. 產出報告到 `cases/XX公司/company-report.md`

### 追加資料 + 增量更新

1. 把新資料丟到 `cases/XX公司/input/`（PDF、截圖、訪談筆記等）
2. 執行 `/supplement XX公司`
3. 系統會讀既有報告 + 新檔案，產出 Supplement Memo 到 `supplements/`
4. 主報告的 Version History 自動更新

### 訪談筆記

推薦使用結構化格式。詳見 `references/methodology/interview-notes-schema.md`。

也可以用 `/meeting` 先結構化逐字稿，再把產出丟進 `input/`。

## Drop Zone 規則

- 檔案優先級最高（高於 web 搜尋結果），但仍須交叉驗證
- 支援：PDF、PNG/JPG、MD/TXT、HTML
- `input/` 子目錄被 `.gitignore` 排除，不會推上 git
- 引用格式：`[來源: cases/{target}/input/{filename}]`

完整規範見 `references/methodology/drop-zone.md`。

## 隱私

`cases/*/` 全部被 `.gitignore` 排除。只有本 `README.md` 和 `_case-template.md` 會被 tracked。

你可以安心放年報、合約、訪談筆記等敏感檔案。
