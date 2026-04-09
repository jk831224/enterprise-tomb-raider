---
name: industry
description: >
  產業分析快捷入口（路徑 A）。使用者說「/industry XX」時觸發。
  直接進入產業研究，跳過路徑判斷。
argument-hint: "[產業名稱]"
allowed-tools: Read Glob Grep WebSearch WebFetch Write Edit Agent
---

# 產業分析 — 路徑 A 快捷入口

## Step 0: 使用者 Profile 檢查

按 `.claude/skills/recon/SKILL.md` 的 Step 0 邏輯執行（檢查 `.claude/user-profile.md` 是否存在，不存在則觸發 onboarding 或跳過）。

## 執行流程

1. 分析目標：`$ARGUMENTS`（如果為空，問使用者想研究哪個產業）
2. 快速 Scoping：確認「產業細分 + 地理範圍 + 分析目的」（1 輪以內完成，0 輪最好）
3. 確認後，載入 `references/methodology/scale-classification.md` 取得規模適配規則
4. **執行 `.claude/skills/recon/SKILL.md` 的 Step 3.5 Drop Zone Scan**（掃描 `cases/{產業名稱}/input/`）
5. 按 `.claude/skills/recon/SKILL.md` 的 Step 4 路徑 A 流程執行
6. 品質 Review 後，按 `.claude/skills/recon/SKILL.md` 的 Step 5.5 產出決策簡報（僅當 profile 存在）

所有執行規格（`agent/AGENT-CORE.md`）、品質標準（`output-quality.md`）、存檔規則同 recon。
