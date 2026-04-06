# Changelog

所有版本變更紀錄。格式參考 [Keep a Changelog](https://keepachangelog.com/)。

## [v1.1] — 2026-04-06

新增 User Profile 與 Decision Brief 機制：從「給你資訊」進化到「告訴你這對你意味著什麼」。

### 新增

- **User Profile（使用者設定檔）**
  - 首次使用任何 Skill 時觸發 onboarding（1 輪 4 題，可跳過）
  - 儲存角色、產業背景、決策情境、特殊關注
  - 支援「更新我的 profile」隨時修改
  - 檔案位於 `.claude/user-profile.md`，已加入 .gitignore

- **Decision Brief（決策簡報）**
  - 品質 Review 後的新階段，基於完成的報告 + User Profile 產出
  - 五種角色鏡頭：投資人 / 求職者 / 合作夥伴 / 競品分析師 / 其他
  - 六段結構：一句話判斷、三件重要的事、紅旗警示、特殊關注回應、該問的問題、下一步行動
  - 零搜尋預算，完全基於已有報告重新解讀
  - 證據等級從主報告繼承，不升級不降級

### 修改

- `agent/AGENT-ROUTES.md`：兩條路徑各新增 Decision Brief 階段
- `.claude/skills/recon/SKILL.md`：新增 Step 0（profile 檢查）、Step 5.5（Decision Brief）
- `.claude/skills/company/SKILL.md`、`industry/SKILL.md`：同步新增 Step 0 和 Decision Brief
- `.claude/rules/output-quality.md`：新增 `decision-brief` report-type 和特殊規則
- `references/methodology/quality-checklist.md`：新增 5 項 Decision Brief 檢查項目
- `.claude/settings.json`：新增 user-profile.md 讀寫權限
- `CLAUDE.md`、`docs/architecture.md`：同步更新流程圖和結構說明

## [v1.0] — 2026-04-06

首次公開版本。完整的產業與公司情報研究工作流。

### 系統架構
- Skill / Agent / Reference 三層分離架構
- 三個入口指令：`/recon`（統一入口）、`/industry`（產業分析）、`/company`（公司分析）
- Agent 自主執行迴圈：搜尋 → 驗證 → 交叉比對 → 結構化產出

### 研究能力
- 路徑 A：產業 → 公司（宏觀到微觀）
- 路徑 B：公司 → 產業（以公司為錨點的產業分析）
- 規模自適應：微型 / 中型 / 大型上市公司自動切換分析框架
- 四級證據標記：充分證據 / 部分證據 / 推測待驗證 / 資料缺失

### 執行層
- AGENT-CORE：角色定義、迴圈邏輯、token 預算、降級策略、錯誤處理
- AGENT-ROUTES：路徑與階段清單
- 四個階段 prompt：實體驗證、利害關係人調查、產業分析、公司深度分析

### 知識層
- 方法論：路徑選擇、規模分類、品質檢查、產業特定來源策略、fetch 政策
- 報告模板：產業報告、公司報告
- 案例沉澱機制與標準模板

### 品質控制
- Rules 自動生效（output-quality.md）
- 報告檔名規範、來源追蹤、證據等級標記、語言規範
