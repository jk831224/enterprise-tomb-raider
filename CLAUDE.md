# Enterprise Tomb Raider — 企業祖墳探勘器

產業與公司深度分析工具。用於投資決策、求職評估、合作判斷等情報研究場景。

## 使用方式

- `/recon [目標]`：統一入口，自動判斷路徑並執行完整研究流程
- `/industry [產業名稱]`：直接進入產業分析
- `/company [公司名稱]`：直接進入公司分析

## 專案結構

- `agent/AGENT-CORE.md`：執行核心（角色、迴圈、預算、降級、錯誤處理）
- `agent/AGENT-ROUTES.md`：路徑與階段清單
- `agent/prompts/`：各階段 prompt，由 skill 按階段動態載入
- `references/`：共用知識層（方法論、報告模板、實戰案例）
- `output/`：報告產出
- `docs/`：架構文件、設計意圖、歷史 review（不在執行路徑上）
