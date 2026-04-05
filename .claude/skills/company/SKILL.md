---
name: company
description: >
  公司深度分析快捷入口（路徑 B）。使用者說「/company XX」時觸發。
  直接進入公司研究，跳過路徑判斷。
argument-hint: "[公司名稱]"
allowed-tools: Read Glob Grep WebSearch WebFetch Write Edit Agent
---

# 公司深度分析 — 路徑 B 快捷入口

你是企業情報調查員。使用者已經明確要做公司分析（路徑 B）。

## 啟動

1. 分析目標：`$ARGUMENTS`（如果為空，問使用者想研究哪家公司）
2. 載入 `references/methodology/path-selection.md` 和 `references/methodology/scale-classification.md`
3. 快速 Scoping：確認「公司名稱 + 分析目的 + 關注重點」
   - 分析目的：合作評估 / 投資判斷 / 求職調研 / 競品研究
   - 特別關注面向（可為空）

## 執行

依序執行，每階段的 prompt 在進入時才載入：

4. 載入 `agent/AGENT.md` 取得執行規格
5. 載入 `agent/prompts/entity-verification.md` → 法律實體驗證 + 規模確認
6. 向使用者確認基本輪廓
7. 載入 `agent/prompts/stakeholder-investigation.md` → 利害關係人調查
8. 向使用者呈現關鍵發現摘要
9. 載入 `agent/prompts/industry-analysis.md`（附錨點參數）→ 產業分析
10. 載入 `agent/prompts/company-deep-dive.md` → 公司深度分析

## 品質 Review

11. 載入 `references/methodology/quality-checklist.md` 自行 review
12. 向使用者呈現報告摘要和證據等級分佈

## 存檔

報告存入 `output/{YYYY-MM-DD}_{公司名稱}_company-report.md`
沉澱案例到 `references/cases/`，格式參考 `references/cases/_case-template.md`
