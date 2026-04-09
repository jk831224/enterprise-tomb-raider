# Enterprise Tomb Raider — 企業祖墳探勘器

產業與公司深度分析工具。用於投資決策、求職評估、合作判斷等情報研究場景。

## 使用方式

- `/recon [目標]`：統一入口，自動判斷路徑並執行完整研究流程
- `/industry [產業名稱]`：直接進入產業分析
- `/company [公司名稱]`：直接進入公司分析
- `/supplement [目標]`：增量更新既有報告（讀取 `cases/{目標}/input/` 新增檔案 → 產出 Supplement Memo + 更新版本鏈）

首次使用會觸發 User Profile 設定（可跳過）。設定後每次分析完成會額外產出 Decision Brief（決策簡報），根據使用者角色解讀報告重點。

## 專案結構

- `agent/AGENT-CORE.md`：執行核心（角色、迴圈、預算、降級、錯誤處理）
- `agent/AGENT-ROUTES.md`：路徑與階段清單
- `agent/prompts/`：各階段 prompt，由 skill 按階段動態載入
- `references/`：共用知識層（方法論、報告模板）
- `cases/`：分析案例統一目錄 — 每家公司/產業一個資料夾，含 `input/`（drop zone）、報告、增量更新、案例紀錄（v1.5，gitignored）
- `product/`：PM 工件層 — PRD、架構文件、流程圖、RFC（設計變更紀錄）、效能報告。**不在執行路徑上**，agent 不應載入
