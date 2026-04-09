# RFC-003: `cases/` 統一目錄 + `/supplement` 增量更新 + 版本鏈

**狀態**：已實作
**日期**：2026-04-09
**作者**：Andrew × Claude
**版本**：v1.5

## 問題

1. 同一家公司的分析資料散落三處（`input/`、`output/`、`references/cases/`），使用者不直覺
2. 分析完成後無法增量追加新資料（獵頭筆記、面試筆記、新聞稿、PDF），只能重跑全流程

## 方案

### `cases/` 統一目錄

每家公司/產業一個資料夾，集中管理所有相關檔案：

```
cases/{target}/
├── input/              # Drop Zone
├── company-report.md   # 主報告（含 Version History）
├── decision-brief.md   # 決策簡報
├── supplements/        # 增量 Memos
└── case-log.md         # 案例沉澱
```

### `/supplement` Skill

讀取既有報告 + 新 drop zone 檔案 → 產出 Supplement Memo + 更新版本鏈。搜尋預算 5 search / 2 fetch。

### 版本鏈

報告 metadata 追蹤版本歷程：v1.0（首次）→ v1.1, v1.2...（supplement）→ v2.0（重跑）。

### 訪談筆記 Schema

YAML frontmatter 定義 `type`、`source`、`confidence`，agent 據此決定證據等級處理方式。

## 遷移

- `input/` → `cases/{target}/input/`
- `output/` → `cases/{target}/`
- `references/cases/case-*.md` → `cases/{target}/case-log.md`
- `.gitignore` 更新為 `cases/*/`

## 受影響檔案

新建 7 個、修改 10 個、遷移 3 組、清理 2 個。詳見計畫文件。

## 設計決策紀錄

| 決策 | 選項 | 選擇 | 理由 |
|------|------|------|------|
| 目錄結構 | input+output 分開 vs 合併 cases/ | 合併 cases/ | 使用者直覺，一個 `ls` 看全貌 |
| 增量更新 | 全量重跑 vs /supplement | /supplement | 節省 20+ 分鐘和搜尋預算 |
| 版本控制 | 多檔案 vs 版本鏈 | 版本鏈 | 主報告不分裂，supplement memo 獨立追蹤 |
| 訪談筆記 | free-form vs schema | schema（YAML） | 讓 agent 自動判斷 confidence → 證據等級 |
| 適用範圍 | 只用在一個 case vs 通用 | 通用 | 所有未來 /company 和 /industry 分析 |
