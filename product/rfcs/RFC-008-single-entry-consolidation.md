# RFC-008：單一入口整併 — 移除 /recon 與 /industry

| 欄位 | 內容 |
|------|------|
| **狀態** | Accepted（2026-06-11 Andrew 口頭提出並核准整併方案） |
| **建立日期** | 2026-06-11 |
| **最後更新** | 2026-06-11 |
| **作者** | Andrew Yen |
| **對應版本** | v2.1 |
| **CHANGELOG entry** | [v2.1](../../CHANGELOG.md#v21) |
| **觸發來源** | 使用者觀察：「最常用的幾乎只有 /company，其他似乎都可以移除」；經實際使用數據驗證後核准 |
| **相關 RFC** | [RFC-007](RFC-007-adversarial-deep-dive-loop.md)（v2.0 深挖輪，本次整併於其上）；[RFC-005](RFC-005-single-context-architecture.md)（架構簡單性原則的延續） |

---

## 1. Summary

把四入口（/recon、/industry、/company、/supplement）整併為雙入口：**/company（唯一研究入口）+ /supplement（增量更新）**。原 recon 主控邏輯（Profile、Scoping、Drop Zone、預分析評估、品質 Review、存檔沉澱）全文併入 company/SKILL.md，使其自包含；/recon 與 /industry 入口刪除（檔案層快照保留）；`industry-analysis.md` prompt 保留，以錨點模式在公司流程內產出產業章節。

## 2. Background / Problem

### 使用數據（2026-06-11 盤點 `cases/`）

| 指標 | 數值 | 含意 |
|------|------|------|
| 實戰案例總數 | 15 | — |
| 公司研究（路徑 B） | **15 / 15** | 路徑判斷從未走向 A |
| 獨立產業分析（路徑 A） | **0** | /industry 與 /recon 的路徑判斷零使用 |
| 含錨點產業章節的案例 | 5 / 15 | industry-analysis prompt 有實際價值，但都在公司流程內 |
| 用過 /supplement 的案例 | 2（AI 社群新創 H、電商 SaaS I） | 增量更新有實戰使用，須保留 |

### 結構問題

- /company 原為薄殼，九成邏輯活在 recon/SKILL.md——每次執行都要跨檔載入兩個 SKILL，且「薄殼 → 引擎」的雙層維護曾造成規格漂移（v1.9.1 審計的 A1 檔名斷鏈即源於此類多處規格不同步）
- 入口數量本身是給使用者的 context：四個指令的選擇成本，在實際使用 100% 走同一條路的情況下是純負擔

## 3. Goals / Non-goals

**Goals**：單一研究入口；company/SKILL.md 自包含；保留全部分析能力（含錨點產業章節）；交叉引用零斷鏈；可退版。

**Non-goals**：不動 agent 層內部的「路徑 B」術語（prompts 內部沿用，僅入口層移除路徑概念）；不移除 /supplement（有實戰使用且為 drop zone 閉環）；不重做 README 全文（只更新入口相關段落）。

## 4. Options Considered

| 選項 | 說明 | 結論 |
|------|------|------|
| A. 不動 | 用不到的入口不觸發就沒成本 | 入口選擇成本與雙層維護漂移風險持續存在 |
| B. 只刪 /industry | 最小風險 | 沒解決薄殼→引擎的雙層結構 |
| **C. 單一入口整併** ⭐ | recon 邏輯併入 /company，刪兩入口 | 符合實際使用型態；消除雙層維護 |

## 5. Decision

**選 C。** 整併原則：

1. **步驟編號不變**：company/SKILL.md 沿用 recon 的 Step 0–6 編號（含 3.5、4.0.5、4.2.5、4.7），所有外部文件引用的座標（drop-zone.md、RFC-006/007、hook 訊息）不需重新對應
2. **路徑判斷移除**：原 Step 2 路徑判斷改為「目標確認」——使用者要產業全景時，說明本工具為單公司深度研究，請其指定錨點公司
3. **能力保留**：`industry-analysis.md`（錨點模式）、`templates/industry-report.md`、output-quality 的 `industry-report` type 全部保留
4. **`path-selection.md` 刪除**（已歸檔）：單一入口下路徑選擇表失去存在意義

### 退版

- 檔案層：整併前的 recon / industry / company SKILL 與 path-selection.md 快照於 `agent/_archive/v2.0-phase1-pre-consolidation/`
- git 層：v2.1 變更未 commit 前可直接還原；commit 後可 revert

## 6. 影響範圍（交叉引用清掃清單）

| 檔案 | 變更 |
|------|------|
| `.claude/skills/company/SKILL.md` | 重寫為自包含主控器（~340 行） |
| `.claude/skills/recon/`、`.claude/skills/industry/` | 刪除（已快照） |
| `references/methodology/path-selection.md` | 刪除（已快照） |
| `.claude/hooks/enforce-stage-prompt-load.sh` | 錯誤訊息 recon → company |
| `references/methodology/drop-zone.md`、`model-selection.md`、`deep-dive-sources.md` | Step 座標指向 company SKILL |
| `agent/AGENT-ROUTES.md` | 移除路徑 A 表；SoT 指向 company SKILL |
| `agent/AGENT-LOOP.md` | 適用範圍與回程座標更新 |
| `references/templates/company-report.md` | 版本規則移除 /recon |
| `.claude/skills/supplement/SKILL.md` | 前提移除 /industry |
| `CLAUDE.md`、`README.md`、`cases/README.md` | 入口敘事改為單一入口 |

**不動**：`agent/prompts/*`（industry-analysis 錨點模式原文保留）、`AGENT-CORE.md`（「Recon Agent」為角色名非入口引用）、RFC-006/007 正文（歷史紀錄不回改）。

## 7. 風險

| 風險 | 緩解 |
|------|------|
| 使用者偶爾真的要產業全景 | Step 2 目標確認提供說法：指定錨點公司，產業脈絡入錨點章節；若未來需求成真，從 `_archive` 還原 /industry 成本極低 |
| 作品集敘事弱化（少了「路徑判斷」賣點） | README 改寫為更強的敘事：「入口數量也是 context，用數據修剪」——以使用數據驅動的減法本身就是 Context Engineering 範例 |
| 外部文件殘留 recon 引用 | 全 repo grep 清掃 + 驗證腳本檢查（見 CHANGELOG v2.1 驗證紀錄） |

## 8. Followups

- `product/PRD.md`、`product/architecture.md` 的入口章節回填（PM 工件層，不在執行路徑，延後不影響運作）
- 首個 v2.1 真實案例驗證：自然語觸發（「幫我研究 XX」）是否正確落到 /company
- 觸發 eval（`evals/trigger-evals.json`）中「幫我研究一下」類模糊查詢的期望值隨單一入口重新檢視
