# CriticVerdict Schema — Critic 回傳格式

> 對抗式深挖輪（v2.0）中，critic subagent 對每個受查 claim 回傳的裁定格式。
> Phase 1 為單票 critic（一個 critic 內部跑完三角度）；Phase 2 將擴為三票多數決。

## JSON Schema

critic 的最終訊息必須是一個 JSON array，每個受查 claim 一個元素：

```json
{
  "target_claim": "受查結論的原文",
  "angle": "source | logic | counterevidence",
  "verdict": "證實 | 證偽 | 存疑",
  "reasoning": "裁定理由（≤100 字）",
  "counter_source": "若證偽：反證來源 URL；否則 null",
  "counter_quote": "若證偽：反證原文截句；否則 null",
  "suggested_evidence_level": "充分 | 部分 | 推測 | 缺失 | maintain"
}
```

## 欄位規則

| 欄位 | 規則 |
|------|------|
| `angle` | 填**決定性**的那個角度：`source`=來源信度不足或有更權威反例；`logic`=推論跳步或存在替代解釋；`counterevidence`=找到相反的公開證據 |
| `verdict` | **找不到反證 ≠ 證實**。「證實」需要找到額外的獨立佐證來源；只是沒找到反證 → 填「存疑」 |
| `counter_source` | 反證來源本身必須可查證（真實 URL、真實內容）。**杜撰反證比漏判更嚴重**——這會污染報告。不確定就填存疑 |
| `suggested_evidence_level` | `maintain` = 維持原等級。升級建議須符合 output-quality 多來源規則 |

## 裁定 → 證據等級調整規則（orchestrator 端執行）

| verdict | 動作 |
|---------|------|
| 證偽（counter_source 可查證） | 降一級（充分→部分→推測→缺失），報告中附反證引用 |
| 證實（附新獨立來源） | 可升一級；升到「充分」須滿足兩個獨立來源規則 |
| 存疑 | 維持原等級，報告中附 critic 理由摘要 |

主 context 對「證偽」裁定的 counter_source 至少抽查 2 個關鍵項（1 次 search/fetch 驗證可達性與內容相符），防 critic 幻覺反證（RFC-007 風險表第 2 項）。
