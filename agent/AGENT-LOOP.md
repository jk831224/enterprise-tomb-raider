# Recon Agent — 對抗式深挖輪（AGENT-LOOP）

> v2.0 Phase 1（RFC-007 Option B）：平行深挖 + 單票 critic。**固定 1 輪**。
> Phase 2（多輪迭代 + completeness critic + 3 票多數決）尚未實作，預留段落在文末。
> 適用範圍：公司深度研究流程（v2.1 起為系統唯一流程）。

## 觸發時機

company-deep-dive 完成、品質 Review（company SKILL Step 5）之前。此時主報告（輪 0 baseline）已存在，深挖輪的任務是把它變得**更廣**（四類來源系統性覆蓋）、**更可信**（獨立證偽）。

## 預算（初稿，待首案校準——RFC-007 §9）

深挖輪不另開預算池，而是用**總預算上限**控管（RFC-007 §5.4 硬上限）：

| 規模 | 總 web_search 上限（含輪 0） | 受查 claims 上限 |
|------|---------------------------|----------------|
| 微型 | 40 | 5 |
| 中型 | 60 | 8 |
| 大型 | 90 | 12 |

**分配演算法**（進入深挖輪時計算一次）：

```
剩餘 = 總上限 − 輪 0 已用 search 數
IF 剩餘 < 8 → 跳過深挖輪，報告標註「深挖輪未執行（預算耗盡）」——這就是防空轉
ELSE:
  每個 explorer 預算 = floor(剩餘 × 0.6 / 4)
  critic 總預算     = floor(剩餘 × 0.25)
  保留              = 其餘（整合階段抽查反證用）
```

範例：微型輪 0 用了 28 → 剩 12 → explorer 各 1-2、critic 3、保留 2。微型公司自然得到「淺挖」，大型公司自然得到「深挖」——規模自適應不靠額外開關。

subagent 模型：**繼承主 session 模型，不降級**（RFC-007 約束：不為省成本用弱模型）。

## 執行流程

### ① 整理 baseline 缺口（主 context，零搜尋）

從輪 0 報告提取兩份清單：

- **待證偽清單**：所有標 `[推測，待驗證]` 與 `[部分證據]` 的結論，按「對最終判斷的影響度」排序，取前 N（上表上限）
- **覆蓋缺口**：四類來源（政府紀錄/公開言論/匿名風評/關聯網絡）各自在輪 0 被覆蓋的程度，寫成一句話摘要傳給對應 explorer，避免重複挖

### ② 平行 spawn 四個 explorer（一則訊息內同時發出）

用 Agent 工具，**同一則訊息發 4 個 spawn** 以並行執行。每個 explorer 的 prompt 模板：

```
你是 {explorer 名}。先 Read agent/subagents/{對應檔}.md，依其規格執行。

目標識別包：
- 登記名稱：{...}／統編：{...}／負責人：{...}
- 關鍵人物：{輪 0 stakeholder 名單}
- 產業：{...}／規模分類：{...}
- （explorer-network 額外）登記地址、董監事完整名單、已知關聯法人

輪 0 已覆蓋：{該來源類的一句話摘要}
本次預算：search ≤{n}、fetch/MCP ≤{m}

回傳：只輸出 Finding[] JSON（格式見 agent/schemas/finding.md），不加任何說明文字。
```

### ③ 整合 findings（主 context）

收齊四份 Finding[] 後：

1. **Schema 驗證**：依 `agent/schemas/finding.md` 的驗證規則逐筆檢查，棄用不合格者並記數
2. **去重**：與輪 0 既有結論重複的 `corroborates` finding → 觸發證據升級評估（新增獨立來源可升一級，升「充分」須兩獨立來源）
3. **衝突**：`conflicts` finding → 進報告衝突表（格式同 annual-report-analysis 的衝突校正表），標明兩說與採用判斷
4. **新發現**：`new` finding → 寫入對應章節，引用格式 `[來源: {source_url}]` + 原文截句入註
5. 報告的 Edit 由主 context 執行（company-deep-dive prompt 已在輪 0 Read，stage discipline hook 不受影響；subagent 一律不寫 `cases/`）

### ④ 平行 spawn critic（每 4 個 claims 一個 critic）

待證偽清單 + 整合後新增的 `[推測]`/`[部分證據]` 結論，依上限截斷後分批：每個 critic 受理 ≤4 claims，同一則訊息並行發出。prompt 模板：

```
你是對抗證偽查核員。先 Read agent/subagents/critic.md，依其規格執行。
受查 claims：{清單，每項含結論原文、現行證據等級、引用來源}
目標公司：{識別包}
預算：每 claim ≤2 search
回傳：只輸出 CriticVerdict[] JSON（格式見 agent/schemas/critic-verdict.md）。
```

### ⑤ 證據等級升降（主 context）

依 `agent/schemas/critic-verdict.md` 的調整規則執行。其中「證偽」裁定的 counter_source 至少抽查 2 個關鍵項（用保留預算驗證可達性與內容相符）——critic 幻覺反證是高風險項，抽查是防線。

### ⑥ 產出對抗驗證摘要（附加於報告末、附錄前）

```
## 對抗驗證摘要（v2.0 深挖輪）

| 項目 | 數值 |
|------|------|
| Explorer findings（採用/棄用） | N / M |
| 新發現 / 佐證 / 衝突 | a / b / c |
| 受查 claims | N |
| 證實 / 證偽 / 存疑 | x / y / z |
| 證據等級升 / 降 | u / d |
| 深挖輪 search 用量 | n（上限 N） |
```

之後回到 company SKILL Step 5 品質 Review，照常進行。

## 失敗處理

- explorer 回傳非 JSON / 解析失敗 → 要求重試一次 → 再失敗放棄該 explorer，摘要標註「{來源類}未完成」
- 單一 explorer 失敗不影響其他三個；四個全失敗 → 報告標註「深挖輪未完成」，照常進品質 Review
- critic 失敗 → 該批 claims 維持原證據等級，標註「未經對抗查核」

## 紀律提醒

進入深挖輪前必須 Read 本檔（同 Stage Discipline 精神——「我記得流程」不是替代品；預算演算法與 prompt 模板的細節就在本檔）。

---

## Phase 2 預留（未實作）

以下機制屬 RFC-007 Option C 增量，本版**不執行**：

- 多輪循環（輪 1..N）+ 邊際遞減終止（連續 1 輪新增充分證據 < 閾值即停：微型 <2 / 中型 <3 / 大型 <5）
- Completeness Critic（每輪找缺口、剪枝死線索、產生下輪目標）
- Critic 3 票多數決（≥2 票判不成立 → 降級）
- 深挖輪上限：微型 2 / 中型 3 / 大型 4 輪
