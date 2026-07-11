# Recon Agent — 路徑與階段

## 路徑 A：產業 → 公司

| 步驟 | 載入 | 動作 | 回傳 |
|------|------|------|------|
| 1 | `prompts/industry-analysis.md` | 產業分析（歷史趨勢 + 結構定位 + 頂級玩家） | 產業報告 → skill 層 |
| 2 | — | 使用者決定是否深入公司 | 若是 → 路徑 B Step 1 |
| 3 | `prompts/decision-brief.md` | 基於報告 + User Profile 產出決策簡報 | 決策簡報 → skill 層（僅當 profile 存在） |

## 路徑 B：公司 → 產業

| 步驟 | 載入 | 動作 | 回傳 |
|------|------|------|------|
| 1 | `prompts/entity-verification.md` | 法律實體驗證 + 規模確認 | 快速輪廓 → skill 確認 |
| — | *（Skill 層）* | **預分析評估**：資源預估 + 模型建議 + 年報計畫 | 分析計畫 → 使用者確認 |
| 1.5 | `prompts/stakeholder-investigation.md` | 三層利害關係人調查 | 調查結果 → skill 確認 |
| 2 | `prompts/industry-analysis.md`（附錨點） | 以公司為錨點的產業分析 | — |
| 2.5 | `prompts/annual-report-analysis.md` | 年報解析（大型=強制、中型=建議、微型=跳過） | 年報數據摘要 + 衝突清單 → company-deep-dive 輸入 |
| 3 | `prompts/company-deep-dive.md` | 整合前序的公司深度分析（含年報數據） | 完整報告 → skill 品質 review |
| 4 | `prompts/decision-brief.md` | 基於報告 + User Profile 產出決策簡報 | 決策簡報 → skill 層（僅當 profile 存在） |

**每個階段的 prompt 在進入時才載入，不要一次全載。**

> **預分析評估為 Skill 層檢查點**，非 Agent 層階段，不載入 prompt，不消耗搜尋預算。
> **年報解析（Step 2.5）** 為條件性階段：大型/上市=強制、中型=建議、微型=跳過。
> **Decision Brief 為可選階段**：僅當 `.claude/user-profile.md` 存在時執行。此階段搜尋預算為零，完全基於已完成的報告進行角色化重新解讀。
