# 設計健檢 — 與 2026 年中主流的對齊度審視

> **健檢日期**：2026-06-08
> **觸發**：使用者提問「年初開發的平台設計，是否已與當前主流脫軌？」
> **性質**：中性健檢留檔（非變更提案）。是否據此動架構，由作者（Andrew）拍板 → 見 §6 決策點。
> **對應版本**：v1.9

---

## TL;DR

**沒有整體脫軌。核心架構（單 context × 單次深度研究）符合 2026 主流「single-agent first」共識，且 context engineering 的兩個槓桿（select/write）做得好、甚至以 RFC-006 hook 領先業界。** 但時間造成了三處具體漂移，按嚴重度：① 模型基準停在 4.6 世代（**確定過時，必修**）；② RFC-005 的「不用 subagent」結論仍對，但**論證前提已被新能力部分推翻**（typed structured output 解決了證據鏈斷裂）；③ verification/critic 已成主流標配，而本專案仍把它列為「候選」。

---

## 1. 評估方法與知識邊界（誠實聲明）

執行健檢的 AI 訓練知識截止為 **2026-01**，本健檢日期為 2026-06。為避免以記憶杜撰「最新趨勢」，當前主流以兩個 ground truth 佐證：

- **環境實況**：本專案運行的 Claude Code 環境本身的工具集（Workflow、Agent/subagent、Skills、MCP、Memory、Hooks、Plan mode）即 2026-06 平台能力的直接證據。
- **Web 查證**：2026 年中公開的 agent 設計文獻（見 §7）。

下文嚴格區分「查證到的事實」與「健檢者的判斷」。

---

## 2. 對照當前主流

### 2.1 Multi-agent 共識（事實）
- 2026 業界主流指引：**「不再是要不要用 multi-agent，而是何時複雜度值得轉換——先用聚焦的 single-agent，當工作需要時再擴展為協作專家團隊」**（Innervation AI、Fungies 2026 guide）。
- 多 agent 五大優勢：domain specialization、parallel processing、**built-in verification**、heterogeneous model selection、graceful failure handling。
- Anthropic 自家多 agent 架構數據：較單 agent **+90.2% 表現、−84% token**（透過四槓桿組合）。

> **判斷**：這條共識**直接支持 RFC-005**。本專案核心場景是「對話式、單次、一家公司」，正是「先 single-agent」適用區。**單 context 不是落後，是正確的起步選擇。**

### 2.2 Context Engineering 四槓桿（事實）
2026 收斂出的框架：**write、select、compress、isolate**，各對應一種失敗模式：
| 槓桿 | 防止 | 本專案現況 | 對齊度 |
|------|------|-----------|--------|
| **select**（just-in-time 載入） | context confusion | prompt 動態載入 + RFC-006 hook 強制 | ✅ **領先**（harness 級強制，多數專案只停在慣例） |
| **write**（外部結構化儲存） | context poisoning | cases/ + `_registry.json` + case-log | ✅ 對齊 |
| **compress**（壓縮歷史） | context distraction | 以 Opus 1M「不壓縮」硬扛迴避 | ◐ 迴避而非主動處理 |
| **isolate**（subagent 隔離） | context clash | **刻意不用**（RFC-005） | ⚠️ 缺口（單次場景可接受） |

> **事實**：主流現在「subagent 回傳 **typed output**（fact / episode / recommendation / tool result），非 prose summary」。**這正是 RFC-005 Option A 最大缺陷（summary-only 斷證據鏈）的解法**，且由 schema 機制在工具層自動完成，不需 RFC-005 Option B 預估的 3-5 小時自建 findings schema。

### 2.3 Verification / Critic 範式（事實）
- Agent/Critic pattern、Chain-of-Verification（把驗證拆成一連串問題）、adversarial testing（矛盾工具結果、malformed data）已是 2026 可靠性標配。
- **「Deterministic checks at base: schema, format, citation validity」** — 引文有效性檢查被列為測試金字塔的基層。

> **判斷**：本專案的證據等級標記、強制交叉驗證、`[資料缺失]` 紀律，**精神上已對齊** citation-validity 主流；但「主動找反證」的 critic 角色（PRD 候選「Adversarial cross-checking」）仍未實作。主流已把 built-in verification 當標配，本專案還在候選。

---

## 3. 三層判斷：對齊 / 有意取捨 / 真實落差

| 類別 | 項目 | 說明 |
|------|------|------|
| ✅ **對齊或領先** | Skills 入口、MCP 整合、prompt 動態載入（select）、cases/registry（write）、**RFC-006 hook 強制紀律**、證據鏈/citation 紀律、規模自適應、降級標註 | 這些是 2026 主流核心實踐，且 hook 防線、證據紀律屬領先水準 |
| 🟰 **有意取捨（不算脫軌）** | 單 context、不用 subagent | 符合「single-agent first」共識；對單次深度研究，證據鏈與預算彈性 > isolate 的省 token。RFC-005 結論成立 |
| ⚠️ **真實落差** | ① 模型基準過時 ② RFC-005 論證前提被新能力推翻 ③ verification/critic 仍在候選 ④ isolate 槓桿缺席（卡住 roadmap 兩個候選功能） | 見 §4、§5、§6 |

---

## 4. 確定的過時點：模型基準（P0，純事實過時）

- `product/perf/baseline-v1.1-model-comparison.md`（2026-04-06）整份以 **Opus 4.6 / Opus 4.6 (1M)** 為最高階基準；`recon/SKILL.md` Step 4.0.5 預分析評估的模型決策樹建議「大型/上市 → Opus 4.6 (1M)」。
- **現況**：最新為 **Opus 4.8**（本次健檢即在其上運行）。Sonnet 4.6 / Haiku 4.5 在當前仍是有效型號，**故非全表過時——過時的是 Opus 4.6 → 4.8 這條線**，以及據此計算的 token 經濟學（定價、1M context 行為可能已變）。
- **影響**：預分析評估會向使用者建議一個已被取代的型號名稱；RFC-005 §6 的 token 經濟學以 4.6 定價計算，回本期結論需重算。

---

## 5. RFC-005 重檢

**結論仍成立，但理由需更新。**

| RFC-005 原論證 | 2026-06 重檢 |
|---------------|-------------|
| Option A subagent「summary-only → 證據鏈斷裂」 | **部分推翻**：typed structured output 讓 subagent 回傳含 URL/年份/原文/證據等級的結構化資料，證據鏈可保留。不再是「subagent 必然斷鏈」 |
| Option B「自建 findings schema 成本 3-5 小時、ROI 差」 | **成本大降**：schema validation 已是工具層原生能力（Workflow/Agent 的 schema 參數），不需自建 |
| 「目前無平行需求」 | **仍成立**：單次研究一家公司是當前唯一場景 |
| 三個重評條件（平行需求 / context 壓力 / 展示需求） | 條件①（平行分析 ≥3 家）**已在 PRD roadmap**（「多公司比較模式」候選）。一旦啟動，Workflow pipeline 是現成正解 |

> **判斷**：不需要為現有「單次研究」流程導入 subagent——那會犧牲證據鏈彈性換取單次場景用不到的 isolate。但 **RFC-005 的書面論證應更新**，把「subagent 弱化證據鏈」修正為「我們的單次場景不需要 isolate 槓桿」，以免未來誤引為「subagent 一律有害」的通則（RFC-005 §7 風險表自己也預警了這點）。

---

## 6. 建議行動（決策權保留給作者）

> 以下是健檢建議，非既定變更。動工與否、是否開 RFC，由 Andrew 拍板。

**P0 — 確定該做、低成本、純維護**
- 更新 `baseline-*-model-comparison.md` 與預分析評估模型決策樹：Opus 4.6 → 4.8，重算 token 經濟學。**這是事實過時，不涉架構爭議。**

**P1 — 重檢決策、中等價值**
- 起草 **RFC-007**：重檢 RFC-005，更新「subagent 證據鏈」論證（§5）；明確「多公司比較 / adversarial cross-check 一旦啟動，採 Workflow pipeline + typed output，而非改造現有單次流程」。把 verification 從「候選」升為「近期」。
- 把 context engineering 四槓桿術語（write/select/compress/isolate）寫進 `architecture.md`，明確專案對 compress（1M 硬扛）與 isolate（暫不採用）的立場——讓「沒做」變成「有意識地沒做」。

**P2 — 順勢而為、看需求觸發**
- **Adversarial cross-checking 試點**：以本次微型公司 G研究為例——報告中多個 `[推測]`（49% 股東、營收區間、2024 增資用途）正是 critic subagent 的理想標的：spawn 一個 verifier 對每個推測「找一個反證或證偽來源」。這同時補上 §2.3 的 verification 缺口，且用 Workflow 幾乎零架構成本。
- 評估 case-log 從「手動讀取」升級為 memory 自動 recall（對齊原生 memory 機制）。

---

## 7. 來源

**Web 查證（2026-06）**：
- [Single vs. Multi-Agent Architecture: The 2026 Guide — Innervation AI](https://www.innervationai.com/blog/single-vs-multi-agent-architecture-2026-guide/)
- [AI Agent Orchestration Developers Guide 2026 — Fungies](https://fungies.io/ai-agent-orchestration-developers-guide-2026/)
- [Context Engineering: Agent Reliability Playbook 2026 — Digital Applied](https://www.digitalapplied.com/blog/context-engineering-agent-reliability-playbook-2026)
- [Context Engineering 2026 Field Guide — Taskade](https://www.taskade.com/blog/context-engineering)
- [Complete Guide to LLM & AI Agent Evaluation 2026 — Adaline](https://www.adaline.ai/blog/complete-guide-llm-ai-agent-evaluation-2026)
- [AI Agent Design Patterns — Microsoft Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)

**環境 ground truth**：本專案運行的 Claude Code 工具集（Workflow / Agent / Skills / MCP / Memory / Hooks）。

**專案內部**：`product/architecture.md`、`product/PRD.md`、`product/rfcs/RFC-005`、`product/rfcs/RFC-006`、`product/perf/baseline-v1.1-model-comparison.md`。

---

> **一句話收尾**：你年初的設計沒有過時——它在 select/write/紀律三個維度甚至領先；真正該做的不是「追上 multi-agent 潮流」，而是 ① 把模型基準更新到 4.8、② 把「為什麼不用 subagent」的論證從舊前提改寫成新前提、③ 把 verification 從候選變成近期實作。前者是維護，後兩者才是這次健檢真正的價值。
