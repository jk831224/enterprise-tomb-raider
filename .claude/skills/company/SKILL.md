---
name: company
description: >
  公司深度分析快捷入口（路徑 B）。使用者說「/company XX」時觸發。
  直接進入公司研究，跳過路徑判斷。
argument-hint: "[公司名稱]"
allowed-tools: Read Glob Grep WebSearch WebFetch Write Edit Agent
---

# 公司深度分析 — 路徑 B 快捷入口

## Step 0: 使用者 Profile 檢查

按 `.claude/skills/recon/SKILL.md` 的 Step 0 邏輯執行（檢查 `.claude/user-profile.md` 是否存在，不存在則觸發 onboarding 或跳過）。

## 執行流程

1. 分析目標：`$ARGUMENTS`（如果為空，問使用者想研究哪家公司）
2. 分析目的：使用者已表達則記錄，否則預設「全面分析」，不主動詢問
3. 確認後，載入 `references/methodology/scale-classification.md` 取得規模適配規則
4. 按 `.claude/skills/recon/SKILL.md` 的 Step 4 路徑 B 流程執行，**包含**：
   - entity-verification 完成後，執行 **Step 4.0.5 預分析評估**（見 recon/SKILL.md）
   - industry-analysis 完成後，依規模執行 **Step 4.2.5 年報解析**（見 recon/SKILL.md）
5. 品質 Review 後，按 `.claude/skills/recon/SKILL.md` 的 Step 5.5 產出決策簡報（僅當 profile 存在）

所有執行規格（`agent/AGENT-CORE.md`）、品質標準（`output-quality.md`）、存檔規則同 recon。
