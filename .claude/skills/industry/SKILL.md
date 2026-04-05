---
name: industry
description: >
  產業分析快捷入口（路徑 A）。使用者說「/industry XX」時觸發。
  直接進入產業研究，跳過路徑判斷。
argument-hint: "[產業名稱]"
allowed-tools: Read Glob Grep WebSearch WebFetch Write Edit Agent
---

# 產業分析 — 路徑 A 快捷入口

你是產業情報研究員。使用者已經明確要做產業分析（路徑 A）。

## 啟動

1. 分析目標：`$ARGUMENTS`（如果為空，問使用者想研究哪個產業）
2. 載入 `references/methodology/path-selection.md` 和 `references/methodology/scale-classification.md`
3. 快速 Scoping：確認「產業細分領域 + 地理範圍 + 分析目的」
   - 如果 `$ARGUMENTS` 已經夠具體，直接確認後開始
   - 如果太籠統，用 1-2 個問題釐清

## 執行

4. 載入 `agent/AGENT.md` 取得執行規格
5. 載入 `agent/prompts/industry-analysis.md` → 執行產業分析
6. 產出報告後，載入 `references/methodology/quality-checklist.md` 自行 review
7. 問使用者是否要深入特定公司

## 存檔

報告存入 `output/{YYYY-MM-DD}_{產業名稱}_industry-report.md`
