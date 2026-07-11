---
name: company
description: >
  公司深度分析快捷入口（路徑 B）。使用者輸入「/company XX」時必定觸發；
  使用者明確指名要對某家公司做深度研究、盡職調查、背景調查時也應觸發
  （例：「幫我盡調 XX」「查一下 XX 這家公司的底細」「XX 公司能不能去／能不能投／能不能合作」）。
  直接進入公司研究流程：實體驗證 → 利害關係人 → 產業錨點 → 年報 → 深度分析 → 對抗式深挖輪（v2.0）。
  模糊需求（未指名特定公司）請改走 /recon 做路徑判斷。
argument-hint: "[公司名稱]"
allowed-tools:
  - Read
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - Write
  - Edit
  - Agent
  - "Bash(node ~/mission-control/cli.js*)"
  - mcp__tw-data__tw_company_lookup
  - mcp__tw-data__tw_person_network
  - mcp__tw-data__headless_fetch
---

# 公司深度分析 — 路徑 B 快捷入口

本 skill 是薄入口：路徑已確定為 B，其餘全部委派 `recon` 主控流程執行。不要在這裡複製 recon 的步驟細節——單一事實來源是 `.claude/skills/recon/SKILL.md`。

## Step 0: Mission Control 開票 + 使用者 Profile

1. 向 Mission Control 開票（`kanban add --status doing` + `research-start` event，route 填 B；指令見專案 CLAUDE.md「開票規則」）
2. 按 `.claude/skills/recon/SKILL.md` 的 Step 0 邏輯執行 Profile 檢查（`.claude/user-profile.md` 不存在則觸發 onboarding 或跳過）

## 執行流程

1. 分析目標：`$ARGUMENTS`（如果為空，問使用者想研究哪家公司）
2. 分析目的：使用者已表達則記錄，否則預設「全面分析」，不主動詢問
3. 載入 `references/methodology/scale-classification.md` 取得規模適配規則
4. 執行 `.claude/skills/recon/SKILL.md` 的 **Step 3.5 Drop Zone Scan**（掃描 `cases/{公司名稱}/input/`）
5. 按 `.claude/skills/recon/SKILL.md` 的 **Step 4 路徑 B 流程**執行，包含：
   - entity-verification 完成後 → **Step 4.0.5 預分析評估**（資源預估 + 模型建議 + 年報計畫）
   - industry-analysis 完成後，依規模 → **Step 4.2.5 年報解析**
   - company-deep-dive 完成後 → **Step 4.7 對抗式深挖輪**（v2.0：4 explorer 平行深挖 + critic 證偽，Read `agent/AGENT-LOOP.md`）
6. 按 recon **Step 5 品質 Review** → **Step 5.5 決策簡報**（僅當 profile 存在）→ **Step 6 存檔與案例沉澱**（含教訓回寫檢查與 Mission Control 完成回報）

所有執行規格（`agent/AGENT-CORE.md`）、品質標準（`.claude/rules/output-quality.md`）、存檔規則同 recon。

## 依賴清單（本 skill 不可獨立安裝）

本 skill 依賴同 repo 內的：`.claude/skills/recon/`、`agent/`（CORE / ROUTES / LOOP / prompts / subagents / schemas）、`references/methodology/`、`references/templates/`、`.claude/rules/output-quality.md`、`.claude/hooks/enforce-stage-prompt-load.sh`。打包安裝到其他環境不會運作。
