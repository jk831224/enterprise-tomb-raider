# RFC-007：對抗式深挖循環 — 從線性六階段到自適應 deep-dive loop

| 欄位 | 內容 |
|------|------|
| **狀態** | Accepted（2026-06-11 Andrew 於 /company 技能升級審批中核准 Scope B＝Phase 1 落地；Phase 2 待首案驗收後另啟） |
| **建立日期** | 2026-06-08 |
| **最後更新** | 2026-06-11 |
| **作者** | Andrew Yen |
| **對應版本** | v2.0 |
| **CHANGELOG entry** | [v2.0](../../CHANGELOG.md#v20)（待 release 回填） |
| **PRD 章節** | [PRD § 設計原則](../PRD.md) |
| **相關 commit** | branch `v2.0-adversarial-loop`（待 commit 後回填） |
| **觸發來源** | 2026-06-08 對話：設計健檢（[design-health-review-2026-06](../design-health-review-2026-06.md)）發現 verification + isolate 兩個槓桿缺口；使用者要求「在合法合規下讓挖掘公司功能更深、更廣、更可信」 |
| **相關 RFC** | 更新 [RFC-005](RFC-005-single-context-architecture.md)（單 context 決策的重評）；整合 [RFC-006](RFC-006-stage-discipline-hook.md)（hook 共存） |

---

## 1. Summary

把現有「線性一次過」的六階段研究，升級為「**探勘 → 對抗驗證 → 找缺口 → 再探勘**」的規模自適應循環。透過三個新增引擎——**Explorer 群**（四類來源平行深挖，更廣）、**Critic 群**（多票對抗證偽，更可信）、**Completeness Critic + 循環控制器**（迭代逼近 OSINT 天花板，更深）——同時拉高研究的深度、廣度與可信度。

關鍵設計約束：① 守住「單次單公司」框架，不擴張到多公司比較；② subagent 一律回傳 **typed structured output**（含 URL／原文／證據等級），保住證據鏈，化解 RFC-005 的核心顧慮；③ **規模自適應終止**防止微型公司空轉（C 路線最大風險）；④ 保留全部現有方法論資產與 PRD 五大不可妥協原則；⑤ 全程 Opus 4.8，不為省成本用弱模型。

實作走 **B→C 漸進**：Phase 1 先落地「平行深挖 + 單票 critic」，Phase 2 再加「迭代循環 + 多票對抗」。

---

## 2. Background / Problem

### 觀察到的問題

兩條線索匯流：

1. **設計健檢**（2026-06-08）對照 2026 主流，發現本專案 context engineering 四槓桿（write/select/compress/isolate）只做了 select + write，**isolate（subagent 隔離）與 verification（對抗驗證）兩個槓桿缺席**。verification 已是 2026 主流標配（built-in verification、citation-validity 為測試金字塔基層），本專案仍列為候選。
2. **使用者需求**：固定使用 Opus 4.8 + 1M context、不在意成本、不要弱模型，明確要求「在合法合規下讓**挖掘公司**功能更深、更廣、更可信」，並選定最徹底的演進路線（全自動對抗循環）。可深挖的四類來源全數授權：政府公開、公開社群、匿名風評、關聯網絡。

### 現況的限制

以剛完成的微型公司 G（微型）研究為實例，現行線性架構暴露三個天花板：

- **廣度受限於線性注意力**：一次只能挖一條線；四類新來源（裁罰/判決/標案/商標、社群、PTT/Dcard/Glassdoor、關聯持股）沒有系統性覆蓋。微型公司 G的「地方衛生局裁罰個案」「員工真實風評」「49% 隱形股東」都只到「待查/推測」。
- **可信度靠自審**：證據等級由同一個 agent 自評，無獨立對抗。報告留下多個 `[推測]`（49% 股東、營收區間、增資用途）無人主動證偽。
- **深度一次到底、無回補**：搜尋飽和即停，沒有「發現缺口 → 再挖」的迭代。OSINT 天花板裡「理論可推斷但沒做到」的項目（TIPO 商標、衛生局裁罰系統直查）就此遺漏。

---

## 3. Goals / Non-goals

### Goals

- **G1 更廣**：四類來源 explorer **平行**深挖，系統性覆蓋政府公開／公開社群／匿名風評／關聯網絡
- **G2 更可信**：多票對抗 critic **主動證偽**每個 `[推測]`/`[部分證據]`，降低不確定標記比例、強化 citation validity
- **G3 更深**：completeness critic + 迭代循環，逼近 OSINT 天花板（把「理論可推斷但漏掉」變成「已挖」）
- **G4 守住證據鏈**：subagent 一律 typed structured output，不因隔離而斷鏈（RFC-005 顧慮的解法）
- **G5 防空轉**：規模自適應終止，微型公司自然收斂、不在死線索上浪費
- **G6 保留資產 + 可退版**：複用六階段 prompt/methodology/templates；雙層退版保護

### Non-goals

- **不做多公司比較 / 產業全景 / 競品矩陣**（守單次單公司；那是另一條路線，需獨立 RFC）
- **不破壞 PRD 五大不可妥協原則**（誠實／強制交叉驗證／缺失明示／數據源優先序／成本透明）
- **不為省成本用弱模型 / sub-agent 降級**（使用者明確全程 Opus 4.8；本 RFC 與 model-comparison 的性價比結論脫鉤）
- **不突破付費牆 / 反爬蟲 / 肉搜非公開個資**（合規紅線；關聯網絡只用公開登記與公開報導）

---

## 4. Options Considered

### Option A：方法論深化（零架構變動）

純在六階段 prompt 內擴充四類來源搜尋樣式 + 加「自我反證」步驟。
**優點**：零風險、純 markdown、最快、完全相容 RFC-005。
**缺點**：深挖與驗證仍線性，受單一注意力限制；self-verification 有盲點（自審自己）；「更廣」未真正解決。

### Option B：驗證層 + 平行深挖（擴增式 subagent）

主流程不動，只在「平行深挖」與「對抗查核」兩點擴增 subagent，typed output 保證據鏈。
**優點**：補上兩個槓桿缺口；證據鏈保全；與 RFC-005 不衝突（擴增非替代）。
**缺點**：需 subagent 定義 + 編排 + typed schema；單票 critic 仍可能漏判。

### Option C：全自動對抗式深挖循環（在 B 上加迭代 + 多票）⭐ 選定

B + 迭代循環（loop-until-dry）+ completeness critic + 3 票對抗 critic。
**優點**：深廣可信一次到位、最逼近 OSINT 天花板、最大化 Opus 4.8 + 1M 優勢。
**缺點**：複雜度最高；**對微型公司有空轉風險**（本 RFC 用規模自適應終止解決）；終止條件需謹慎設計。

---

## 5. Decision

**選擇：Option C，但以 B 為 Phase 1 漸進落地。**

**理由**：使用者要的「深+廣+可信」三者同時最大化，只有 C 能完整覆蓋；A 沒解決廣度與客觀驗證，B 缺迭代深度。C 的唯一硬傷「空轉」是可設計掉的工程問題（見 §5.4 終止條件），不構成否決理由。漸進 B→C 讓風險可控、每階段可獨立驗收與退版。

**被犧牲的東西**：架構簡單性（從「純 markdown 線性」變成「subagent 編排 + 循環」，mental model 變重）；單次研究的 wall-clock 變長（使用者已表明不在意）。

### 5.1 架構總覽

```
/company {目標}
   │
   ▼
[預分析評估]  ← 保留（PRD 原則7），升級為呈現「預估輪數 + 規模自適應上限 + 總預算」
   │ 使用者確認後，循環自動跑（不再每輪打斷）
   ▼
┌─────────────────── 對抗式深挖循環（主 context 編排）───────────────────┐
│                                                                        │
│  輪 0（基礎輪）：現有線性六階段快跑 → baseline findings + 報告骨架        │
│                                                                        │
│  輪 1..N（深挖輪）：                                                     │
│    ① Completeness Critic 找缺口 → 本輪探勘目標                           │
│    ② Explorer 群【平行】深挖（4 類來源 + 缺口）→ typed findings           │
│    ③ 主 agent 整合 findings、更新報告（證據鏈留主 context）               │
│    ④ Critic 群【3 票對抗】證偽推測 → 升/降證據等級                        │
│    ⑤ 終止判斷（規模自適應，見 §5.4）→ 收斂則跳出                          │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
   │
   ▼
[品質 Review] → [Decision Brief] → [存檔 + Mission Control]  ← 全部沿用
```

### 5.2 組件設計

| 組件 | 類型 | 職責 | 載體 |
|------|------|------|------|
| **Orchestrator** | 新增（主 context） | 驅動循環、規模自適應終止、預算控管、進度播報 | skill 層 + AGENT-CORE 循環邏輯 |
| **Explorer 群** | 新增 subagent ×4+ | 各包一類來源獨立深挖，回傳 typed findings | 原生 Agent 工具，playbook = 現有/新增 prompt |
| **Critic 群** | 新增 subagent ×3 | 三角度對抗證偽（來源信度／邏輯／反證），多數決 | 原生 Agent 工具 |
| **Completeness Critic** | 新增 subagent ×1 | 每輪找缺口、剪枝死線索、產生下輪目標 | 原生 Agent 工具 |
| **整合層** | 沿用主 agent | 持有全部 typed findings（證據鏈）、用現有模板產報告 | 現有 |

**Explorer 分工**：`explorer-gov`（裁罰/判決/標案/TIPO商標/進出口/匯報）、`explorer-social`（創辦人高管公開社群、演講、Podcast、專訪）、`explorer-sentiment`（PTT/Dcard/Glassdoor/比薪水，**強制標來源信度**）、`explorer-network`（配偶/親屬持股、關聯法人、股權公開線索，**只用公開資料**）。現有 entity/stakeholder/industry/company prompt 作為核心 explorer 的領域 playbook 複用。

**Critic 三角度**：`critic-source`（來源夠權威嗎？有更權威的反例嗎？）、`critic-logic`（推論跳步了嗎？有替代解釋嗎？）、`critic-counterevidence`（有相反的公開證據嗎？）。**≥2 票判不成立 → 降級或標記**。

### 5.3 資料流與證據鏈（typed structured output）

每個 explorer/critic 回傳 schema（草案，待 writing-plans 細化）：

```
Finding {
  claim: string              // 結論陳述
  dimension: enum            // entity/stakeholder/industry/finance/legal/...
  source_url: string         // 來源連結
  source_quote: string       // 原文截句（保證據鏈可追溯）
  evidence_level: enum       // 充分/部分/推測/缺失
  cross_refs: string[]       // 交叉驗證的其他來源
}
CriticVerdict {
  target_claim: string
  angle: enum                // source/logic/counterevidence
  verdict: enum              // 證實/證偽/存疑
  counter_source: string?    // 若證偽，反證來源（本身須可查證）
}
```

主 context 持有所有 Finding（含 source_quote），下游 company-deep-dive「回扣產業脈絡」與 output-quality 的來源追蹤**都有原始引用可用**——這就是 RFC-005 最擔心的斷鏈問題的解法。

### 5.4 防空轉：規模自適應終止（C 的核心）

四重終止條件，任一觸發即停深挖輪：

| 機制 | 微型 | 中型 | 大型 |
|------|------|------|------|
| **深挖輪上限** | 2 輪 | 3 輪 | 4 輪 |
| **邊際遞減**（主信號）：連續 1 輪新增「充分證據」結論 < 閾值即停 | <2 | <3 | <5 |
| **死線索剪枝**：completeness critic 標記「已試無果」維度，不重挖 | ✓ | ✓ | ✓ |
| **預算硬上限**（最後保險）：總 web_search | ≤40 | ≤60 | ≤90 |

→ 微型公司（如微型公司 G，18 search 即飽和）會在輪 1–2 自然收斂，不空轉。**規模分類沿用 scale-classification.md，零新概念。**

### 5.5 互動模式與成本透明（張力處理）

「全自動」≠「無 checkpoint」。化解與 PRD 原則7 的張力：
- **事前**：預分析評估保留並升級——呈現預估輪數、規模自適應上限、總預算
- **事中**：每輪結束以 `log` 播報（本輪挖了什麼、新增幾個結論、證據升降），**不停等**
- **事後**：完整報告 + 對抗驗證摘要 + 證據等級分布
→ 自動跑但全程透明。

### 關鍵決策點（待 Andrew 審定）

1. **載體**：原生 Agent 工具（推薦，可攜）vs Workflow 工具（更 deterministic 但環境依賴）。預設原生。
2. **終止閾值**：§5.4 的數字為初稿，需首個真實案例校準。
3. **RFC-006 hook 調整方式**：見 §8。
4. **匿名風評權重**：強制 `[部分證據]` 上限、不可單獨升級為事實——是否足夠保守？
5. **輪 0 是否必要**：或直接從 explorer 群冷啟動？預設保留輪 0 以建報告骨架。

---

## 6. 效能影響

### 設計時預估

| 維度 | 變更前（v1.9 線性） | 變更後（v2.0 循環） | Δ |
|------|------|------|---|
| 預載 token | 現況 | + subagent 定義/orchestrator | 小增 |
| subagent spawn 次數 | 0 | 微型 ~6-8 / 中型 ~10-14 / 大型 ~16-22 | 大增（本就是目的） |
| web_search 次數 | 微型 ~18 | 微型 ≤40（上限約束） | 增，受規模上限封頂 |
| wall-clock | 線性累加 | explorer 並行 → 非線性 | 平行抵消部分增長 |
| `[推測]` 比例 | baseline | **預期下降**（critic 證偽） | 改善 |
| `[充分]` 比例 | baseline | **預期上升**（多來源交叉） | 改善 |
| 命中率（RFC-002） | baseline | 可能略降（探索性搜尋變多） | 需觀察 exploration ratio |

### 實測結果

> 首個真實案例後回填。建議用**微型公司 G（微型，已有 v1.9 報告可對照）** + 一家中型，雙案例驗收深廣可信三維度的實際改善。

---

## 7. 風險

| 風險 | 嚴重度 | 緩解方式 |
|------|--------|---------|
| **微型公司空轉** | 高 | §5.4 規模自適應終止（本 RFC 核心設計） |
| **critic 幻覺反證** | 高 | critic 的 counter_source 本身須可查證、走交叉驗證，標證據等級 |
| **匿名風評信度低污染報告** | 中 | 強制標 `[部分證據]`/`[推測]`，不可單獨升級為事實 |
| **關聯網絡碰個資** | 中 | 只用公開登記/公開報導，不揭露非公開個資，遵 fetch-policy 黑名單 |
| **subagent 編排複雜度** | 中 | B→C 分期；Phase 1 先驗證證據鏈不斷 |
| **RFC-006 hook 衝突** | 中 | §8 明確調整 hook 邏輯 |
| **typed schema 與現有模板不一致** | 低 | schema 欄位對映 output-quality 必填元素，writing-plans 細化 |

---

## 8. Implementation Plan

### 退版 / 留檔策略（雙層）
- **git 層**（已完成）：main 凍結 v1.9 + v1.9 tag；改造在 `v2.0-adversarial-loop` branch。退版 = `git checkout main`。
- **檔案層**：改造任一現有執行檔（`agent/prompts/*`、`AGENT-CORE.md`、`SKILL.md`）前，先複製 v1.9 快照到 `agent/_archive/v1.9/`，改造期間可 side-by-side 對照。
- **分期 tag**：Phase 1 完成 tag `v2.0-phase1`，Phase 2 完成 tag `v2.0`。

### Phase 1（= Option B 核心）— 平行深挖 + 單票 critic
**新增**：
- `agent/subagents/explorer-{gov,social,sentiment,network}.md` — 四類來源 explorer playbook
- `agent/subagents/critic.md` — 單票對抗 critic
- `agent/schemas/finding.md`、`critic-verdict.md` — typed output schema
- `agent/AGENT-LOOP.md` — orchestrator 編排規格（輪 0 + 單輪深挖 + 整合）

**修改**：
- `.claude/skills/{recon,company}/SKILL.md` — 啟用 Agent spawn、串接 explorer/critic
- `.claude/hooks/enforce-stage-prompt-load.sh` — 調整為認得「主 agent 整合時 Read playbook」或 subagent typed 產物（**待決：§5.5 決策點3**）
- `references/methodology/` — 新增四類來源的搜尋樣式矩陣

### Phase 2（= Option C 增量）— 迭代循環 + 多票對抗
**新增**：
- `agent/subagents/completeness-critic.md` — 缺口發現 + 死線索剪枝
- 擴 `AGENT-LOOP.md` — 多輪循環 + §5.4 規模自適應終止 + 3 票對抗多數決

**修改**：
- 預分析評估（SKILL Step 4.0.5）— 升級呈現預估輪數/上限/總預算
- `product/PRD.md`、`architecture.md`、`CHANGELOG.md`、`RFC-005`（重評註記）

### 不動的檔案
- `references/templates/*`（報告模板複用）、`scale-classification.md`、`quality-checklist.md`、`output-quality.md`、Mission Control 整合、`scripts/sync-registry.py`

---

## 9. Followups / Open Questions

- 終止閾值（§5.4）首案校準後回填實測
- RFC-006 hook 的最終調整方案（§5.5 決策點3）
- 是否將 explorer 的四類來源矩陣抽成獨立 methodology 檔供其他專案複用
- Phase 2 後評估「多公司比較」是否值得開新 RFC（C 的 explorer/critic 可水平複用）
- 本 RFC 對 RFC-005 的關係：是 update 還是 supersede？（傾向 update——RFC-005 對「線性單次」仍成立，本 RFC 是「擴增式」新場景）

## 10. References

- [design-health-review-2026-06](../design-health-review-2026-06.md) — 觸發本 RFC 的健檢
- [RFC-005](RFC-005-single-context-architecture.md) — 單 context 決策（本 RFC 重評其前提）
- [RFC-006](RFC-006-stage-discipline-hook.md) — Stage Discipline Hook（本 RFC 需整合）
- 2026 主流佐證：context engineering 四槓桿（write/select/compress/isolate）、built-in verification、typed subagent output（健檢 §7 來源）
- 2026-06-08 對話：需求釐清（深+廣+可信、四類來源全開、選定 Option C、留退版空間）
