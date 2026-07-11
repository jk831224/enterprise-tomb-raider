# Recon Agent — 階段順序

> 本表為摘要視圖。階段順序的單一事實來源是 `.claude/skills/company/SKILL.md` Step 4——兩者不一致時以 SKILL 為準並回報修正本表。
> v2.1 起為單一入口架構（原路徑 A／路徑判斷已隨 /recon、/industry 移除，見 RFC-008）。`industry-analysis.md` prompt 保留，以錨點模式在公司流程內產出產業章節。

## 公司深度研究流程（原路徑 B）

| 步驟 | 載入 | 動作 | 回傳 |
|------|------|------|------|
| 1 | `prompts/entity-verification.md` | 法律實體驗證 + 規模確認 | 快速輪廓 → skill 確認 |
| — | *（Skill 層）* | **預分析評估**：資源預估 + 模型建議 + 年報計畫 | 分析計畫 → 使用者確認 |
| 1.5 | `prompts/stakeholder-investigation.md` | 三層利害關係人調查 | 調查結果 → skill 確認 |
| 2 | `prompts/industry-analysis.md`（附錨點） | 以公司為錨點的產業分析 | — |
| 2.5 | `prompts/annual-report-analysis.md` | 年報解析（大型=強制、中型=建議、微型=跳過） | 年報數據摘要 + 衝突清單 → company-deep-dive 輸入 |
| 3 | `prompts/company-deep-dive.md` | 整合前序的公司深度分析（含年報數據） | baseline 報告（輪 0） |
| 3.5 | `AGENT-LOOP.md` | **對抗式深挖輪**（v2.0：4 explorer 平行 + critic 證偽） | 更新後報告 + 對抗驗證摘要 → skill 品質 review |
| 4 | `prompts/decision-brief.md` | 基於報告 + User Profile 產出決策簡報 | 決策簡報 → skill 層（僅當 profile 存在） |

**每個階段的 prompt 在進入時才載入，不要一次全載。**

> **預分析評估為 Skill 層檢查點**，非 Agent 層階段，不載入 prompt，不消耗搜尋預算。
> **年報解析（Step 2.5）** 為條件性階段：大型/上市=強制、中型=建議、微型=跳過。
> **Decision Brief 為可選階段**：僅當 `.claude/user-profile.md` 存在時執行。此階段搜尋預算為零，完全基於已完成的報告進行角色化重新解讀。
